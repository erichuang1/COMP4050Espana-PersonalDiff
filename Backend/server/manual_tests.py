import src.file_management as fm
import src.job_subsystem as js
import src.controllers.question_generation_queries as qgenqueries
import src.ai.viva_questions as viva
import src.ai.pdf_to_text as ptt
import src.ai.rubric_gen as rubric
import src.formatting as formatting
import json
import os
import boto3

def readAllLines(path:str)->str:
    out = ''
    with open(path, 'rt') as fp:
        for line in fp:
            out += line
    return out

testAIOutput = {
            "analysis_evaluation": {
                "question_1": "How does the concept of hardware acceleration relate to the development of analog computing as discussed in your assignment?",
                "question_2": "Evaluate the advantages and disadvantages of using analog computers over digital ones based on your findings.",
                "question_3": "Discuss the impact of Moore's Law on modern computing hardware and how it relates to your exploration of analog computing."
            },
            "application_problem_solving": {
                "question_1": "Assuming you have a basic patch-panel analog computer, how would you configure it to solve a specific application problem? Provide an example from your assignment."
            },
            "factual_recall": {
                "question_1": "Can you explain the key differences between analog and digital computers based on the content of your assignment?",
                "question_2": "What are the main components of an analog computer as detailed in your paper?",
                "question_3": "What does the term 'analog fitness' refer to in the context of your project?"
            },
            "open_ended": {
                "question_1": "Considering the future of computing, what do you believe are the most significant implications of hybrid analog-digital computing systems for software development?"
            }
        }

testQnsFile = {
        "submission_id": 451,
        "unit_code": 'COMP4051',
        "project_title": 'the harris zone',
        "random_questions": [
            {
                "question": "What... is your name?"
            },
            {
                "question": "What... is your quest?"
            },
            {
                "question": "What... is the air-speed velocity of an unladen swallow?"
            }
        ],
        "static_questions": [
            "Where are you",
            "What is your favourite samyang flavor"
        ],
        "ai_questions": testAIOutput
    }

testRegenFile = {
    "factual_recall": {
        "regenerated_question_1": "What are the specific values and operations used in the algorithm for calculating the sums of sub-matrices in the approach you outlined, and how do these contribute to the performance of the algorithm?"
    },
    "open_ended": {
        "regenerated_question_1": "In light of the recursive algorithm you have developed for optimizing matrix processing, how might methodologies similar to Agile support teams in adapting their strategies in response to unforeseen complications in such algorithms over the next five years?"
    }
}

testJsonFilePath = '_TESTFILES/test.json'
testPdfFilePath_A = '_TESTDOCUMENTS/comp3010.pdf'
testPdfFilePath_B = '_TESTDOCUMENTS/DUMMY_FILE.pdf'
testTxtFilePath = '_TESTDOCUMENTS/TEST.txt'
testRemoteFilePath = 's3://4050backendfilestorage/comp3010_5.pdf'
                       
s3 = boto3.client('s3')
print("Test driver running!")
s3_bucket_name = ''
openai_key = ''
organization = ''
project = ''
if os.path.isfile('.keys'):
    print("Loading keys...")
    with open('.keys') as fp:
        keyDict = json.load(fp)

    s3_bucket_name = keyDict['s3_bucket_name']
    openai_key = keyDict['OPENAI_API_KEY']
    organization = keyDict['OPENAI_ORG_KEY']
    project = keyDict['OPENAI_PROJ_KEY']

else:
    print("Gathering keys...")

    s3_bucket_name = input("s3 bucket name: ")
    openai_key = input("openAI api key: ")
    organization = input("openAI organization: ")
    project = input("openAI project: ")

fm.initialise(s3, s3_bucket_name)
keys = {
        "OPENAI_API_KEY":openai_key,
        "OPENAI_ORG_KEY":organization,
        "OPENAI_PROJ_KEY":project
    }

js.initialise(1,1,False,s3,s3_bucket_name, keys)
js._debugUseLocalAddr = True
js._doSingleThread = True
print ("Test driver online!")

sampleRubricCriteria = [
    {
      "criterion": "Process Management",
      "keywords": ["processes", "scheduling", "multithreading"],
      "competencies": ["understanding of process lifecycle"],
      "skills": ["solve synchronization issues"],
      "knowledge": ["scheduling algorithms", "process synchronization"]
    },
    {
      "criterion": "Memory Management",
      "keywords": ["virtual memory", "paging", "segmentation"],
      "competencies": ["memory allocation strategies"],
      "skills": ["apply virtual memory concepts"],
      "knowledge": ["paging", "memory allocation"]
    },
    {
      "criterion": "File Systems",
      "keywords": ["file system architecture", "file allocation"],
      "competencies": ["file system design"],
      "skills": ["optimize file systems"],
      "knowledge": ["file allocation methods", "disk scheduling"]
    }
  ]

sampleUlos = [
    "ULO1: Understand core OS concepts like process, memory, and file systems.",
    "ULO2: Apply OS algorithms to solve problems.",
    "ULO3: Critically evaluate OS architectures.",
    "ULO4: Solve OS concurrency and synchronization problems."
  ]

sampleJobParmie ={
            'assignment_title': 'marts current fav music',
            'submission_id' : 0,
            'file_path' : '_TESTDOCUMENTS/McRaeThesis.pdf',
            'unit_name': 'marts smarts',
            'student_year_level': 'fourth year',
            'no_of_questions_factual_recall': 3,
            'no_of_questions_analysis_evaluation': 3,
            'no_of_questions_open_ended': 3,
            'no_of_questions_application_problem_solving': 3,
            'no_of_questions_conceptual_understanding' : 3,
            'question_challenging_level': 'Challenging',
            'assignment_content': None
        }

sample_job = js._SubsystemJob(1, js._SJobType.VIVA_GEN, sampleJobParmie)
