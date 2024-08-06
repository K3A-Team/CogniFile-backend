from Core.Shared.Database import Database , db
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import json


TEXT_PROMPT = '''
You are an intelligent system designed to optimize folder structures. You will be given a JSON representation of a current folder hierarchy. Your task is to analyze this structure and propose a more organized hierarchy.

Rules and guidelines:
1- You can create new folders and subfolders as needed.
2- You can rename existing folders to better reflect their contents.
3- You must not create any new files.
4- You must not modify or rename any existing files.
5- Group related files into appropriate folders.
6- Consider creating folders based on file types, dates, or common themes.
7- Aim for a logical and intuitive structure that would make it easy for a user to find files.
8- Provide your restructured hierarchy in the same JSON format as the input.

Here's the current folder structure:
{current_structure}

Please analyze this structure and provide a new, optimized JSON representation of the folder hierarchy.
Provide only the JSON and no need for an explanation
'''

PROMPT_TEMPLATE = ChatPromptTemplate.from_template(TEXT_PROMPT)

MODEL_TEMP = 0.0
MODEL = ChatGoogleGenerativeAI(model="gemini-1.5-pro",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

def get_folder_hierarchy(folder_id):
    folder_ref = db.collection('folders').document(folder_id)
    folder_doc = folder_ref.get()
    
    if not folder_doc.exists:
        return None
    
    folder_data = folder_doc.to_dict()
    hierarchy = {
        #'type': 'folder',
        #'id': folder_id,
        'name': folder_data.get('name', ''),
        'children': [],
        'files': []
    }
    
    # Get files
    if 'files' in folder_data:
        file_refs = [db.collection('files').document(file_id) for file_id in folder_data['files']]
        file_docs = db.get_all(file_refs)
        for file_doc in file_docs:
            if file_doc.exists:
                file_data = file_doc.to_dict()
                hierarchy['files'].append({
                    #'type': 'file',
                    #'id': file_doc.id,
                    'name': file_data.get('name', '')
                })
    
    # Recursively get subfolders
    if 'subFolders' in folder_data:
        for subfolder_id in folder_data['subFolders']:
            subfolder = get_folder_hierarchy( subfolder_id)
            if subfolder:
                hierarchy['children'].append(subfolder)
    
    return hierarchy

def optimize_hierarchy(folder_id):
    
    # Building and sending the prompt
    folder_hierarchy = json.dumps(get_folder_hierarchy(folder_id))
    llm_prompt = PROMPT_TEMPLATE.format_messages(
        current_structure = folder_hierarchy
    )
    llm_result = MODEL.invoke(llm_prompt)
    
    # Hnadeling the JSON (langchain offers some way to structure the JSON so this will likely change)
    start = llm_result.content.index('{')
    end = llm_result.content.rindex('}') + 1
    json_str = llm_result.content[start:end]
    json_str = json_str.replace('```json\n', '').replace('\n```', '')
    parsed_json = json.loads(json_str)
    return json.loads(json_str)