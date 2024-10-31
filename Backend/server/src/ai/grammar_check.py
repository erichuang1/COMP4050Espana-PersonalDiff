from openai import OpenAI
import json

# Initialise OpenAI client
client = None

# Method for initialising openAI client
def init_openai(openai_api_key, openai_org_key, openai_proj_key):
    global client
    client = OpenAI(
        api_key=openai_api_key,
        organization=openai_org_key,
        project=openai_proj_key
    )

def grammer_score(input_data):
    
    # Check if OpenAI client is initialized
    if not client:
        return False, "OpenAI client not initialized, refer to README.md"

    try:
        promt = f"""
        Assessing the quality of the written submission in terms of structure, grammar and spelling.
        Assess the quality of the written document in aspects such as: 
        structure appropriate to the type of document, appropriate set of vocabulary, grammar and spelling. 
        For example: a thesis is expected to have A title page, Introduction, TOC, chapters, reference list, in-text citations, register, style level, etc.
        Based on the document below, provide a single numeric score out of 100 in JSON.
        {input_data}
        """

        # OpenAI API Call for question regeneration
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": promt}
            ],
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        response = completion.choices[0].message.content
        try:
            processed_response = process_ai_response(response)
            return processed_response
        except Exception as e:
            return f"Error processing AI response: {e}"
        
        # return processed_response
    except Exception as e:
        return False, f"Error evaluating score: {str(e)}"


def process_ai_response(response):
    try:
        response_data = json.loads(response)
        if 'error' in response_data:
            return False, response_data['error']
        return True, response
    except json.JSONDecodeError:
        return False, "Invalid response from AI"