from django.conf import settings
from openai import OpenAI
import os

def get_json_schema():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'schema.json')
    with open(file_path, 'r') as file:
        return file.read()

def openAI_translate(jp_text: str):

    client = OpenAI(
        base_url = settings.TRANSLATION_MODEL_PROVIDER_URL,
        api_key = settings.TRANSLATION_MODEL_API_KEY,
    )
    
    try:
        response = client.chat.completions.create(
            model= settings.TRANSLATION_MODEL,
            messages=[
                #to turn off reasoning for qwen3-235b-a22b: add /no_think at the beginning of system prompt,
                #to turn off reasoning for glm-4.5-air: add /nothink at the end of each user prompt,
                {"role": "system", "content": "You are an experienced Japanese to English translator. For a given user prompt, translate the Japanese text into English. Do not add any explanation."},
                {"role": "user", "content": jp_text}
            ],
            reasoning_effort = settings.TRANSLATION_MODEL_REASONING_EFFORT
        )
        return response.choices[0].message.content

    except:
        if response and response.choices:
            print(response.choices[0].message.content) 
        result = None    
    
    return result

    
def openAI_analyze(jp_text: str):
    client = OpenAI(
        base_url = settings.TRANSLATION_MODEL_PROVIDER_URL,
        api_key = settings.TRANSLATION_MODEL_API_KEY,
    )
    
    try:
        response = client.chat.completions.create(
            model= settings.TRANSLATION_MODEL,
            messages=[
                #to turn off reasoning for qwen3-235b-a22b: add /no_think at the beginning of system prompt,
                #to turn off reasoning for glm-4.5-air: add /nothink at the end of each user prompt,
                {"role": "system", "content": "You are an experienced Japanese to English translator. For a given user prompt, " +
                "break down the Japanese text using Bunsetsu and do morphological analysis for each of them. Return the result in JSON using this schema. Do not add any text before or after the JSON." + get_json_schema()},
                {"role": "user", "content": jp_text}
            ],
            reasoning_effort = settings.TRANSLATION_MODEL_REASONING_EFFORT
        )
        result = response.choices[0].message.content.lstrip("```json").rstrip("`")        

    except:
        if response and response.choices:
            print(response.choices[0].message.content) 
        result = None    

    return result