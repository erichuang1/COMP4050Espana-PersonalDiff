# Job Subsystem
# By Harris C. McRae, 2024
#
# Initializes a separate threaded monitor process which
# manages a queue of jobs to be submitted to an AI function
# package. There may be one or more queues based on the queue priority;
# i.e a "slow queue" which only submits a job every N jobs from the
# "standard queue".h
#
# Most functions will return a SubsystemStatus enum as an info code. See the
# definition of SubsystemStatus below.

from enum import Enum
from typing import List
from threading import Thread
from time import sleep
from datetime import datetime

import requests
import json
import os
from botocore.exceptions import ClientError
import src.file_management as fm
import src.ai.viva_questions as viva
import src.ai.pdf_to_text as ptt
import src.ai.rubric_gen as rubric
import src.formatting as format

class SubsystemStatus(Enum):
    """An enum of all return codes used in the job subsystem."""
    # Status codes
    OKAY = 0                        # All is well.
    NO_JOBS = 1                     # No jobs are currently in the queue.
    COMPLETED_JOB = 2               # A job has just been completed and ready to update databases.
    AWAITING_INSTANCE = 3           # Currently waiting for an available instance.
    SHUTDOWN = 4                    # Subsystem has been shutdown

    # Error codes
    INVALID_INPUT = -1              # Provided input is invalid
    NOT_INITIALISED = -2            # The subsystem has not been initialised.
    NOT_DEFINED = -3                # The function has not been fully defined yet.
    UNKNOWN_ERR = -4                # An unknown error occurred.
    NO_SAVED_FILE = -5              # There is no saved queue on disk.
    AI_SYS_ERROR = -6               # An error occurred in the AI subsystems
    FM_SYS_ERROR = -7               # An error occurred in the FileManagement system
    REMOTE_SYS_ERROR = -8           # An error occurred when trying to connect to remote storage
    DB_SYS_ERROR = -9               # An error occurred when trying to connect to databases
    WRONG_JOB = -10                 # Wrong job was passed to a certain function.

class _SJobType:
    """An enum of all job types."""
    UNDEFINED = 0
    VIVA_GEN = 1
    VIVA_REGEN = 2
    RUBRIC_GEN = 3
    RUBRIC_CONVERT = 4

_jobTypeHasFiles = { _SJobType.VIVA_GEN, _SJobType.VIVA_REGEN, _SJobType.RUBRIC_CONVERT }
_jobTypeIsViva = { _SJobType.VIVA_GEN, _SJobType.VIVA_REGEN }
_jobTypeIsRubric = { _SJobType.RUBRIC_GEN, _SJobType.RUBRIC_CONVERT }

class _SubsystemJob:
    jobID:int
    filePath:str
    jobType:_SJobType
    data:dict

    def __init__(self, jID:int, jtype:_SJobType, data:dict):
        self.jobID = jID
        self.jobType = jtype
        self.data = data

    def serialize(self):
        return json.dumps((self.jobID, self.jobType, self.data))
    
    def deserialize(self, data):
        self.jobID, self.jobType, self.data = json.loads(data)
    
            

# Internal Variables
_globalJobCounter: int = -1                 # The global job ID counter. Each job has a unique ID.
_jobSubsystemState: SubsystemStatus = SubsystemStatus.NOT_INITIALISED

# Multi-threaded specific variables
_jobSubsystemRunning: bool = False
_jobSubsystemStartShutdown: bool = False
_jobSubsystemFrequency: float = 0
_jobQueue: List[_SubsystemJob] = []         # A queue of jobs that are waiting for an available instance.
_threadObj:Thread = None                    # The thread object.

# Debug settings
_barSubmit:bool = False                     # Debug value : enable this to stop jobs from escalating to the generation state.
_debugUseLocalAddr:bool = False              # Debug value : enable this to use local files instead of remote for testing.
_doSingleThread:bool = True                 # TURN THIS TO TRUE TO DISABLE THE SECOND THREAD OBJECT

# Misc settings
_downloadFileBeforeUse:bool = True          # Enables downloading files from S3 instance before passing them to AI functions.

def _submit_job(job:_SubsystemJob)->(SubsystemStatus, dict):
    global _jobSubsystemState

    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState,''

    success:bool
    result:str
    file_content = None

    if job.jobType in _jobTypeHasFiles:
        
        if not _debugUseLocalAddr:
            
            if _downloadFileBeforeUse:
                # Download the PDF file from s3 to a local path
                status, local_pdf_path = fm.download_file_from_s3(job.data['file_path'])
                if status != fm.FileStatus.OKAY or not local_pdf_path:
                    return SubsystemStatus.NO_SAVED_FILE, ''
                
                # Open and proces the local file
                with open(local_pdf_path, 'rb') as file:
                    file_content = ptt.extract_text_and_tables_from_pdf(file)
                    
                # Clean up the local file after processing
                if os.path.exists(local_pdf_path):
                    os.remove(local_pdf_path)
                    
            else: # load from remote
                file_content = ptt.extract_text_and_tables_from_pdf(fm.get_pdf_binary_file(job.data['file_path']))
                
        else: # load from local, debug mode
            file = open(job.data['file_path'], mode='rb')
            if not file:
                return SubsystemStatus.NO_SAVED_FILE, ''
            file_content = ptt.extract_text_and_tables_from_pdf(file)
            file.close()

        if file_content is None:
            return SubsystemStatus.FM_SYS_ERROR, "Error with file encoding or reading."
        
        if job.jobType == _SJobType.VIVA_GEN:           # VIVA QN GEN
            job.data["assignment_content"] = file_content
            print("Printing the input we send to AI: ", job.data)
            success, result = viva.generate_viva_questions(job.data)
        elif job.jobType == _SJobType.VIVA_REGEN:       # VIVA QN REGEN
            job.data["assignment_content"] = file_content
            success, result = viva.regenerate_questions(job.data)

        elif job.jobType == _SJobType.RUBRIC_CONVERT:   # RUBRIC CONVERT
            job.data["marking_guide"] = file_content
            result = rubric.convert_rubric(job.data)
            success = result is not None
    else:
        if job.jobType == _SJobType.RUBRIC_GEN:         # RUBRIC GEN
            result = rubric.generate_rubric(job.data)
            success = result is not None
            
    if not success:
        result = f"An error occurred: {str(result)}"
        return SubsystemStatus.AI_SYS_ERROR, result

    if type(result) is str:
        result = json.loads(result)
    if job.jobType in _jobTypeIsViva:
        result = format.correct_ai_output(result)
        
    return SubsystemStatus.OKAY, result
    
def _process_completed_job(job:_SubsystemJob, data:dict)->SubsystemStatus:
    """Processes a completed job appropriately."""

    if job.jobType in _jobTypeIsViva:
        return _process_viva(job, data)
    elif job.jobType in _jobTypeIsRubric:
        return _process_rubric(job, data)
    else:
        return SubsystemStatus.NOT_INITIALISED
    
def _process_viva(job:_SubsystemJob, data:dict)->SubsystemStatus:
    """Processes a completed job, saving the given file to disk and updating databases appropriately."""
    import src.controllers.qgen_queries as qgen_queries

    if job.jobType not in _jobTypeIsViva:
        return SubsystemStatus.WRONG_JOB

    if job.jobType is _SJobType.VIVA_REGEN:
        status,data = zipper_merge_dict(job, data)
        if status != SubsystemStatus.OKAY:
            return status
    
    combined_questions = qgen_queries.package_all_questions(job.data["submission_id"], data)
    name = job.data["assignment_title"] + '_generated_' + datetime.now().strftime("%d%m%Y_%H:%M:%S")

    status, s3_path = fm.create_json_file(name + '.json', combined_questions, rename=True)

    if status != fm.FileStatus.OKAY:
        return SubsystemStatus.FM_SYS_ERROR
    
    # Dump the JSON data to the S3 object
    # try:
    #     s3.put_object(Bucket=S3_BUCKET_NAME, Key=s3_path, Body=json.dumps(combined_questions), ContentType='application/json')
    # except ClientError as e:
    #     print(f"Error uploading JSON data to S3: {str(e)}")
    #     return SubsystemStatus.REMOTE_SYS_ERROR
    
    qgen_queries.upload_generated_files(job.data["submission_id"], name, s3_path, 'GENERATED')
    return SubsystemStatus.OKAY

def _process_rubric(job:_SubsystemJob, data:dict)->SubsystemStatus:
    """Processes a completed rubric job, saving data and updating databases."""
    import src.controllers.rubric_queries as rgenqueries
    import src.controllers.marking_guide_queries as mrgenqueries

    
    if data.get("rubric_title") is not None:
        name = data["rubric_title"]
        
    name = name + '_rubric_' + datetime.now().strftime("%d%m%Y_%H:%M:%S")
    idx = 201
        
    filename = name + ".json"
    if not _debugUseLocalAddr:
        status, s3_path = fm.create_json_file(filename, data, rename=True)
        if status != fm.FileStatus.OKAY:
            return SubsystemStatus.FM_SYS_ERROR

        # # Dump the JSON data to the S3 object
        # try:
        #     s3.put_object(Bucket=S3_BUCKET_NAME, Key=s3_path, Body=json.dumps(data), ContentType='application/json')
        # except ClientError as e:
        #     print(f"Error uploading JSON data to S3: {str(e)}")
        #     return SubsystemStatus.REMOTE_SYS_ERROR

        if job.jobType is _SJobType.RUBRIC_GEN:
            msg,idx = rgenqueries.upload_generated_rubric(job.data["staff_email"], name, filename, s3_path, 'GENERATED')
        elif job.jobType is _SJobType.RUBRIC_CONVERT:
            msg,idx = mrgenqueries.upload_generated_rubric_from_mg(job.data["staff_email"], name, filename, s3_path, 'GENERATED', job.data['marking_guide_id']) 
    else:
        with open(name + '.json', mode='w') as fp:
            json.dump(data, fp, indent=4)

    if idx == 201:
        return SubsystemStatus.OKAY
    return SubsystemStatus.DB_SYS_ERROR

def _process()->SubsystemStatus:
    """At regular periods of time, checks to see if a job can be passed to the AI functions."""
    global _jobSubsystemRunning, _jobSubsystemState, _jobQueue, _jobWaiting, _jobSubsystemFrequency, \
           _jobSubsystemStartShutdown, _instanceCount, _barSubmit

    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState

    while _jobSubsystemRunning:
        if _jobSubsystemStartShutdown:
            break
        
        sleep(_jobSubsystemFrequency)

        # Check if the queue is empty or not; if so, sleep for the _jobSubsystemFrequency
        if len(_jobQueue) == 0 or _barSubmit:
            _jobSubsystemState = SubsystemStatus.NO_JOBS
            continue

        _jobSubsystemState = SubsystemStatus.AWAITING_INSTANCE
        jobSubmit = _jobQueue.pop(0)
        status,data = _submit_job(jobSubmit)

        _jobSubsystemState = SubsystemStatus.COMPLETED_JOB
        if status != SubsystemStatus.OKAY:
            # log err
            pass

        _process_completed_job(jobSubmit, data)

        continue

    _jobSubsystemState = SubsystemStatus.SHUTDOWN
    _jobSubsystemRunning = False
    
    return _jobSubsystemState

def initialise(pollRate:float, instanceCount:int = 1, load:bool = False, s3_client=None, s3_bucket_name=None, aiKeys:dict=None) -> SubsystemStatus:
    """Initializes the subsystem process to run at a given poll rate, and target a given number of instances (defaults to 1)."""
    global _jobSubsystemRunning, _jobSubsystemState, _jobQueue, _jobWaiting, _jobSubsystemFrequency, \
           _jobSubsystemStartShutdown, _instanceCount, _threadObj, _globalJobCounter, _url, _barSubmit, \
           s3, S3_BUCKET_NAME

    if instanceCount <= 0 or pollRate < 0:
        return SubsystemStatus.INVALID_INPUT
    
    _globalJobCounter = 0
    _jobSubsystemFrequency = pollRate
    _threadObj = Thread(target=_process, args=[])
    
    _jobSubsystemState = SubsystemStatus.OKAY
    _jobSubsystemRunning = True
    _jobSubsystemStartShutdown = False

    _jobQueue = []
    
    if aiKeys is None:
        viva.init_openai(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_org_key=os.getenv("OPENAI_ORG_KEY"),
            openai_proj_key=os.getenv("OPENAI_PROJ_KEY")
        )

        rubric.init_openai(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_org_key=os.getenv("OPENAI_ORG_KEY"),
            openai_proj_key=os.getenv("OPENAI_PROJ_KEY")
        )
    else:
        viva.init_openai(
            aiKeys.get("OPENAI_API_KEY"),
            aiKeys.get("OPENAI_ORG_KEY"),
            aiKeys.get("OPENAI_PROJ_KEY")
        )
        rubric.init_openai(
            aiKeys.get("OPENAI_API_KEY"),
            aiKeys.get("OPENAI_ORG_KEY"),
            aiKeys.get("OPENAI_PROJ_KEY")
        )
    
    s3 = s3_client
    S3_BUCKET_NAME = s3_bucket_name
    
    if load:
        _load()

    _url = 'https://comp4050espana.onrender.com/generatequestions'

    if not _doSingleThread:
        _threadObj.start()
    
    return SubsystemStatus.OKAY

def shutdown(save:bool = True)->SubsystemStatus:
    """Appropriately shuts down the job subsystem, saving the contents of the subsystem to disk (can be disabled)."""
    global _jobSubsystemRunning, _jobSubsystemState, _jobQueue, _jobWaiting, _jobSubsystemFrequency, \
           _jobSubsystemStartShutdown, _instanceCount, _threadObj, _globalJobCounter
    
    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState
    # trigger a shutdown of the subprocess
    _jobSubsystemStartShutdown = True
    _jobSubsystemFrequency = 0.01
    
    if not _doSingleThread:
        _threadObj.join()
        
    if save:
        _save()
    _jobQueue = None
    _threadObj = None
    _jobSubsystemState = SubsystemStatus.SHUTDOWN
    return _jobSubsystemState

def submit_new_job(subID:int = 0,
                   fp:str = 'UNDF',
                   unit:str = 'UNDF',
                   proj:str = 'UNDF',
                   challenge:str = 'Easy',
                   level:str = 'UNDF',
                   aiQn:int = 3,
                   factualQn:int = 3,
                   conceptQn:int = 3,
                   analysisQn:int = 3,
                   applicationQn:int = 3,
                   openEndQn:int = 3,
                   regenQns:[dict] = None) \
                   -> \
                   (SubsystemStatus, int):
    """ Enqueues a job with the given parameters, returning a SubsystemStatus as well as the job ID.
        If a list of regen questions is passed, it will try to regenerate those questions.
        DEPRECATED. DO NOT USE. DEPRECATED. DO NOT USE.
    """

    global _jobQueue, _globalJobCounter, _jobSubsystemState, _doSingleThread

    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState

    doRegen = False
    if regenQns is not None:
        doRegen = True

    jID = _globalJobCounter
    _globalJobCounter += 1
    
    job = _SubsystemJob(jID)

    job.create_normal(params)
    
    if _doSingleThread:
        status,data = _submit_job(job)
        if status != SubsystemStatus.OKAY:
            return status, data, jID
        return _process_completed_job(job, data), data, jID
    else:
        _jobQueue.append(job)

    return SubsystemStatus.OKAY, jID

def submit_new_viva_gen(subID, submissionFilePath, projName, unitName, unitLevel, challengeLevel, factRecallQns, analysisQns, openQns, applicQns, conceptualQns)->(SubsystemStatus, int):
    """Creates a new viva gen job, returns the job id."""
    global _jobQueue, _globalJobCounter, _jobSubsystemState, _doSingleThread
    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState
    jID = _globalJobCounter
    _globalJobCounter += 1

    data = {
            'assignment_title': projName,
            'submission_id' : subID,
            'file_path' : submissionFilePath,
            'unit_name': unitName,
            'student_year_level': unitLevel,
            'no_of_questions_factual_recall': factRecallQns,
            'no_of_questions_analysis_evaluation': analysisQns,
            'no_of_questions_open_ended': openQns,
            'no_of_questions_application_problem_solving': applicQns,
            'no_of_questions_conceptual_understanding' : conceptualQns,
            'question_challenging_level': challengeLevel,
            'assignment_content': None
        }

    job = _SubsystemJob(jID, _SJobType.VIVA_GEN, data)

    if _doSingleThread:
        status,data = _submit_job(job)
        if status != SubsystemStatus.OKAY:
            return status, data, jID
        return _process_completed_job(job, data), data, jID
    else:
        _jobQueue.append(job)
        return SubsystemStatus.OKAY, jID
    
    
def submit_new_viva_regen(subID, submissionFilePath, projName, unitName, regenReasons, originalJsonFilePath)->(SubsystemStatus, int):
    """Creates a new viva regen job, returns the job id"""
    global _jobQueue, _globalJobCounter, _jobSubsystemState, _doSingleThread
    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState
    jID = _globalJobCounter
    _globalJobCounter += 1

    data = {
        'assignment_title': projName,
		'submission_id' : subID,
		'file_path' : submissionFilePath,
		'unit_name': unitName,	
		'question_reason': regenReasons,
		'assignment_content': None,
        'old_file_path' : originalJsonFilePath
        }
    
    job = _SubsystemJob(jID, _SJobType.VIVA_REGEN, data)

    if _doSingleThread:
        status,data = _submit_job(job)
        data = json.loads(data)
        if status != SubsystemStatus.OKAY:
            return status, data, jID
        return _process_completed_job(job, data), data, jID
    else:
        _jobQueue.append(job)
        return SubsystemStatus.OKAY, jID

def submit_new_rubric_gen(description:str, staffemail:str, criteria:[dict], ulos:[str])->(SubsystemStatus, int):
    """Creates and submits a new rubric gen job, returns the job id"""
    global _jobQueue, _globalJobCounter, _jobSubsystemState, _doSingleThread
    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState
    jID = _globalJobCounter
    _globalJobCounter += 1

    data = {
            'assessment_description' : description,
            'staff_email' : staffemail,
            'criteria' : criteria,
            'ulos' : ulos
        }

    job = _SubsystemJob(jID, _SJobType.RUBRIC_GEN, data)

    if _doSingleThread:
        status,data = _submit_job(job)
        if status != SubsystemStatus.OKAY:
            return status, jID
        return _process_completed_job(job, data), jID
    else:
        _jobQueue.append(job)

    return SubsystemStatus.OKAY, jID

def submit_new_rubric_convert(filepath:str, staffemail:str, ulos:[str], guideid:int)->(SubsystemStatus, int):
    """Creates and submits a new rubric convert job, returns the job id"""
    global _jobQueue, _globalJobCounter, _jobSubsystemState, _doSingleThread
    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState
    jID = _globalJobCounter
    _globalJobCounter += 1

    data = {
            'staff_email' : staffemail,
            'file_path' : filepath,
            'ulos' : ulos,
            'marking_guide' : None,
            'marking_guide_id' : guideid
        }

    job = _SubsystemJob(jID, _SJobType.RUBRIC_CONVERT, data)

    if _doSingleThread:
        status,data = _submit_job(job)
        if status != SubsystemStatus.OKAY:
            return status, jID
        return _process_completed_job(job, json.loads(data)), jID
    else:
        _jobQueue.append(job)

    return SubsystemStatus.OKAY, jID

# Used by pytests, for inserting dummy rubric data
def test_submit_new_rubric_job(staff_email:str,
                          assessment_descript:str,
                          criterions:[dict],
                          ulos:[str], data:[dict])->(SubsystemStatus, int):
    """Used by pytests, for inserting dummy rubric data"""

    global _jobQueue, _globalJobCounter, _jobSubsystemState, _doSingleThread
    
    if _jobSubsystemState == SubsystemStatus.SHUTDOWN or _jobSubsystemState == SubsystemStatus.NOT_INITIALISED:
        return _jobSubsystemState
    
    jID = _globalJobCounter
    _globalJobCounter += 1

    job = _SubsystemJob(jID)
    params = [ jID, assessment_descript, staff_email, criterions, ulos ]
    job.create_rubric(params)

    if _doSingleThread:
        status = SubsystemStatus.OKAY
        if status != SubsystemStatus.OKAY:
            print(data)
            return status, jID
        return fm._process_completed_rubric(job, json.loads(data)), jID
    else:
        _jobQueue.append(job)

    return SubsystemStatus.OKAY, jID

def debug_destroy_waiting()->SubsystemStatus:
    """Destroys all waiting jobs. For debug purposes when testing (prevents a hang if the AI api isn't working)."""
    global _jobWaiting, _instanceCount, _jobSubsystemState

    if _jobSubsystemState == SubsystemStatus.NOT_INITIALISED or _jobSubsystemState == SubsystemStatus.SHUTDOWN:
        return _jobSubsystemState

    return SubsystemStatus.OKAY

def debug_wipe_queue()->SubsystemStatus:
    """Resets the queue. For debug purposes."""
    global _jobQueue

    _jobQueue = []

    return SubsystemStatus.OKAY

def check_subsystem_status()->SubsystemStatus:
    """Gets the current status of the subsystem for diagnostic purposes."""
    global _jobSubsystemState
    
    return _jobSubsystemState

def set_subsystem_frequency(wait:float)->SubsystemStatus:
    global _jobSubsystemFrequency
    if wait < 0:
        return SubsystemStatus.INVALID_INPUT
    _jobSubsystemFrequency = wait
    return SubsystemStatus.OKAY

def _save()->SubsystemStatus:
    """Saves the queue to the .queue file."""
    global _jobQueue

    individual_dumps = map(lambda x:x.serialize(), _jobQueue)
    
    data = json.dumps(list(individual_dumps))
    
    with open('.queue', 'w') as file:
        file.write(data)
        
    return SubsystemStatus.OKAY

def _load()->SubsystemStatus:
    """Loads the queue from a .queue file if present."""
    global _jobQueue, _globalJobCounter

    if not os.path.isfile('.queue'):
        return SubsystemStatus.NO_SAVED_QUEUE
    
    data = ''
    with open('.queue', 'r') as file:
        data = file.read()

    temp_dumps:[str] = json.loads(data)

    mapped = map(create_job_from_json, temp_dumps)
    
    _jobQueue = list(mapped)
    
    for i in _jobQueue:
        if i.jobID > _globalJobCounter:
            _globalJobCounter = i.jobID+1

    return SubsystemStatus.OKAY

def create_job_from_json(json_data:str)->_SubsystemJob:
    """Creates an instance of a job from a given json data string. Single function to make it easier. Returns NONE if it failed."""
    if json_data == '':
        return None
    job = _SubsystemJob(0, 0, '', 0, '', '', '', '')
    job.deserialize(json_data)
    return job

def zipper_merge_dict(job:_SubsystemJob, data:dict)->(SubsystemStatus, dict):
    """Merges a job's response dict with the former question JSON"""
    
    _AI_QN_CATEGORIES = format._AI_QN_CATEGORIES
    
    oldpath = job.data['old_file_path']
    
    status,file = fm.get_file(oldpath)
    
    if status != fm.FileStatus.OKAY:
        return SubsystemStatus.FM_SYS_ERROR
    
    qns = json.load(file)

    old_aiqns = qns.get('ai_questions')
    
    if old_aiqns is None:
        return SubsystemStatus.UNKNOWN_ERR, data
    
    if type(old_aiqns) is str:
        old_aiqns = json.loads(old_aiqns)
    
    for category in _AI_QN_CATEGORIES:
        old_category = old_aiqns.get(category)
        new_category = data.get(category)

        print(f'category is {category}')
        
        if old_category is None or new_category is None:
            continue
        
        for qnkey in new_category.keys():
            norm_qnkey = qnkey.replace('regenerated_','')
            print(f'key is {norm_qnkey}')
            print(f'old qn is  {old_category.get(norm_qnkey)}, new data is {new_category[qnkey]}')
            if old_category.get(norm_qnkey) is None: 
                continue
            old_category[norm_qnkey] = new_category[qnkey]
        
        old_aiqns[category] = old_category
    
    # TODO: we shouldn't need to return the whole questions field, as that's created when calling package, right? just return old_aiqns
    # qns['ai_questions'] = old_aiqns
    return SubsystemStatus.OKAY, old_aiqns


# def zipper_merge_dict(job:_SubsystemJob, data:dict)->(SubsystemStatus, dict):
#     """Merges a job's response dict with the former question JSON"""
    
#     # _AI_QN_CATEGORIES = ['analysis_and_evaluation', 'application_problem_solving', 'factual_recall', 'open_ended', 'conceptual_understanding',
#     #                      'analysis_and_evaluation_questions', 'application_problem_solving_questions', 'factual_recall_questions', 'open_ended_questions',
#     #                      'open_ended_question','conceptual_understanding_questions']
    
#     oldpath = job.data['old_file_path']
    
#     status,file = fm.get_file(oldpath)
#     if status != fm.FileStatus.OKAY:
#         return SubsystemStatus.FM_SYS_ERROR
    
#     qns = json.load(file)
#     old_aiqns = qns.get('ai_questions')
#     print(old_aiqns)

#     _AI_QN_CATEGORIES = [] 
#     for category in old_aiqns:
#         print(category)
#         _AI_QN_CATEGORIES.append(category)
    
#     print("DEBUG",_AI_QN_CATEGORIES)

#     if old_aiqns is None:
#         return SubsystemStatus.UNKNOWN_ERR, data
#     if type(old_aiqns) is str:
#         old_aiqns = json.loads(old_aiqns)

#     for category in _AI_QN_CATEGORIES:
#         old_category = old_aiqns.get(category)
#         new_category = data.get(category)
        
#         if old_category is None or new_category is None:
#             continue
        
#         for qnkey in new_category.keys():
#             norm_qnkey = qnkey.replace('regenerated_','')
#             if old_category.get(norm_qnkey) is None: 
#                 continue
#             old_category[norm_qnkey] = new_category[qnkey]
        
#         old_aiqns[category] = old_category
    
#     # TODO: we shouldn't need to return the whole questions field, as that's created when calling package, right? just return old_aiqns
#     # qns['ai_questions'] = old_aiqns
#     return SubsystemStatus.OKAY, old_aiqns
    
    