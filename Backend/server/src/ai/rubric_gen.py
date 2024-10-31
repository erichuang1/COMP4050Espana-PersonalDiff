import time
from openai import OpenAI
from pydantic import BaseModel
import pandas as pd
import re

# Initialise OpenAI client
client = None

# For Structured outputs:
class Criteria(BaseModel):
   criteria_name:str
   criteria_description: str

class GradeDescriptor(BaseModel):
    mark_min: int
    mark_max: int
    criterion: list[Criteria]

class GradeDescriptors(BaseModel):
    fail: GradeDescriptor
    pass_: GradeDescriptor
    credit: GradeDescriptor
    distinction: GradeDescriptor
    high_distinction: GradeDescriptor

class AssignmentFeedback(BaseModel):
    rubric_title: str
    grade_descriptors: GradeDescriptors

# Method for initialising openAI client
def init_openai(openai_api_key, openai_org_key, openai_proj_key):
    global client
    client = OpenAI(
        api_key=openai_api_key,
        organization=openai_org_key,
        project=openai_proj_key
    )

# Helper method to get list of criterion:
def get_criterion(input_dict):
    criterion = [] # Empty list initiated to store each criteria
    
    for criteria in input_dict['criteria']:
        criterion.append(criteria['criterion'])
        
    return criterion
    
def generate_rubric(input_dict):
    grade_descriptors = "Fail (0-49), Pass(50-64), Credit (65-74), Distinction (75-84), High Distinction (85-100)"

    assessment_criterion = get_criterion(input_dict)
    sys_prompt = f'''
    You are a highly skilled university professor responsible for creating marking rubrics for assessment tasks. 
    You need to create a marking rubric for an assessment based on the information provided below. 
    The grade descriptors are: {grade_descriptors}. The rubric must assess each criteria provided in the list of criterion
    ''' 
    user_prompt = f"""
    Assessment task overview: {input_dict['assessment_description']}

    Criterion to be assessed:
    """
    for i,criteria in enumerate(assessment_criterion):
        user_prompt+= f"\n- Criteria_{i}: {criteria}"   
    
    user_prompt+= """
    \nEnsure each criterion specifically adheres to the list above

    Keywords/Competencies/Skills per Criterion which need to be taken into account: \n
    """

    for criterion in input_dict['criteria']:
        user_prompt += f"{criterion['criterion']}:\n"
        user_prompt += "Keywords: " + ', '.join(criterion['keywords']) + "\n"
        user_prompt += "Competencies: " + ', '.join(criterion['competencies']) + "\n"
        user_prompt += "Skills: " + ', '.join(criterion['skills']) + "\n"
        user_prompt += "Knowledge: " + ', '.join(criterion['knowledge']) + "\n\n"

    user_prompt += "Unit Learning Objectives (ULOs) that the assessment is mapped to:\n"
    for i, ulo in enumerate(input_dict['ulos'], 1):
        user_prompt += f"* {ulo}\n"

    user_prompt += """
    Please return the feedback in the required format such as the one below:

    {
      "rubric_title": "Assessment Rubric for Algorithms and Data Structures",
      "grade_descriptors": {
        "fail": {
          "mark_min": 0,
          "mark_max": 49,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        }, .....
          ]
        },
        "pass_": {
          "mark_min": 50,
          "mark_max": 64,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        },
        "credit": {
          "mark_min": 65,
          "mark_max": 74,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        },
        "distinction": {
          "mark_min": 75,
          "mark_max": 84,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        },
        "high_distinction": {
          "mark_min": 85,
          "mark_max": 100,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        }
      }
    }
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1096,
        # response_format={"type": "json_object"}
        response_format=AssignmentFeedback
    )

    feedback_response = completion.choices[0].message

    # If the model refuses to respond, you will get a refusal message
    if (feedback_response.refusal):
        print(feedback_response.refusal)
        return None
    else:
        parsed= feedback_response.parsed
        feedback_response_json = parsed.model_dump_json()
        return feedback_response_json


def convert_rubric(rubric_input):
    guide = rubric_input["marking_guide"]
    content = get_guide_content(guide)
    grade_descriptors = "Fail (0-49), Pass(50-64), Credit (65-74), Distinction (75-84), High Distinction (85-100)"
    sys_prompt = f'''
    You are a highly skilled university professor responsible for creating marking rubrics for assessment tasks. 
    You need to create a marking rubric for an assessment based on the information provided below.
    For this, you will need to manipulate the information provided below which has been extracted from the marking guide to fit into the standard rubric format featuring MQs Grade Descriptors (F, P,C,D,HD).
    The grade descriptors are: {grade_descriptors}. The rubric must assess each criteria provided in the list of criterion
    ''' 
    user_prompt = f"""
    Criterion to be assessed:
    """
    user_prompt += str(content)
    user_prompt += "Unit Learning Objectives (ULOs) that the assessment is mapped to:\n"
    for ulo in enumerate(rubric_input['ulos'], 1):
        user_prompt += f"* {ulo}\n"
    user_prompt += """
    Please return the feedback in the required format such as the one below:

    {
      "rubric_title": "Assessment Rubric for Algorithms and Data Structures",
      "grade_descriptors": {
        "fail": {
          "mark_min": 0,
          "mark_max": 49,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        }, .....
          ]
        },
        "pass_": {
          "mark_min": 50,
          "mark_max": 64,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        },
        "credit": {
          "mark_min": 65,
          "mark_max": 74,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        },
        "distinction": {
          "mark_min": 75,
          "mark_max": 84,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        },
        "high_distinction": {
          "mark_min": 85,
          "mark_max": 100,
          "criterion": [
            {
              "criteria_name": Criteria_X,
              "criteria_description": ....        },.....
            {
          ]
        }
      }
    }
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=1096,
        # response_format={"type": "json_object"}
        response_format=AssignmentFeedback
    )

    feedback_response = completion.choices[0].message

    # If the model refuses to respond, you will get a refusal message
    if (feedback_response.refusal):
        print(feedback_response.refusal)
        return None
    else:
        parsed= feedback_response.parsed
        feedback_response_json = parsed.model_dump_json()
        return feedback_response_json
  
def get_guide_content(guide_content):
    # Extract the table content from the dictionary
    table_data = guide_content[1]

    # Clean and split table into lines
    lines = []
    for page, content in table_data.items():
        clean_content = re.sub(r'\n+', '\n', content)  # Clean up extra newlines
        lines += clean_content.strip().split('\n')

    data = []

    for line in lines:
        if '|' in line:
            row = [x.strip() for x in line.split('|')]
            data.append(row)

    # Create dataframe
    df = pd.DataFrame(data[1:], columns=data[0])

    # Criteria Name, Total Weightage %, criteria points, associated makrs

    # array_dic = [
    #     {
    #         "Criteria" : "Content",
    #         "Total Weight" : "30%", # Added values in Week13 col
    #         "CP" : [{"Introductiontoteamandproject" : 2},{"Explanationofoveralldesigncriteria": 3}, {...}]
    #     },
    #     {
    #         "Criteria" : "UseofMedia",
    #         "Total Weight" : "16%", # Added values in Week13 col 4+4+4+4 = 16 / total marks 100 => 16%
    #         "CP" : [{"Attention-grabbing(layout,presentationetc.)" : 4},{"Readabilityoftext(fontsize,headings)": 4}, {...}]
    #     },
    #     ...
    # ]
    df = df.replace('', None)  # Replace empty strings with None for better handling
    df = df.replace('-', 0)
    # df = df.dropna()  # Drop any rows that are completely NaN
    print(df)

    total_marks = 0
    array_dic = []
    criteria = ""
    cp = []

    for i in range(len(df)-1):
        
        if df[df.columns[1]][i] == None and df[df.columns[2]][i] == None:
            array_dic.append({
                "criteria" : criteria,
                "marks" : total_marks,
                "cpoints": cp
            })
            cp = []
            total_marks = 0
            criteria = df[df.columns[0]][i] # Criteria
        else:
            # Criteria Point
            cp.append({df[df.columns[0]][i] : df[df.columns[2]][i]})
            total_marks += int(df[df.columns[2]][i]) # Week13 col marks
    return array_dic
