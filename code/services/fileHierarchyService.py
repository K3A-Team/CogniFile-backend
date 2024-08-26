from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os,ast
import json
from typing import Dict, Any
import uuid
from Models.Entities.Folder import Folder
from collections import defaultdict
from Core.Shared.Database import db


MAX_DEPTH = 30  # Set a maximum depth for recursion
MAX_FILES = 30  # Set a maximum number of files to be processed 


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
Provide an array containing two elements : 
1- The optimised JSON representation  
2- A description for the changes you made
'''

PROMPT_TEMPLATE = ChatPromptTemplate.from_template(TEXT_PROMPT)

MODEL_TEMP = 0.0
MODEL = ChatGoogleGenerativeAI(model="gemini-1.5-flash",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

def get_folder_hierarchy(folder_id, displayFileId = False , displayFolderId = False):
    """
    Retrieve the folder hierarchy for a given folder ID.

    This function fetches the folder document from the database using the provided folder ID,
    and constructs a hierarchical structure containing the names of the folders and files.
    It can optionally include file and folder IDs in the hierarchy. The function recursively
    processes subfolders to build the complete hierarchy.

    Args:
        folder_id (str): The unique identifier of the folder to retrieve the hierarchy for.
        displayFileId (bool): Whether to include file IDs in the hierarchy. Defaults to False.
        displayFolderId (bool): Whether to include folder IDs in the hierarchy. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary representing the folder hierarchy with names and optionally IDs.
                        Returns None if the folder does not exist.
    """
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

    if displayFolderId:
        hierarchy['id'] = folder_id
    
    # Get files
    if 'files' in folder_data:
        file_refs = [db.collection('files').document(file_id) for file_id in folder_data['files']]
        file_docs = db.get_all(file_refs)
        for file_doc in file_docs:
            if file_doc.exists:
                file_data = file_doc.to_dict()
                file = {
                    'name': file_data.get('name', '')
                }
                if displayFileId:
                    file['id'] = file_doc.id

                hierarchy['files'].append(file)
    
    # Recursively get subfolders
    if 'subFolders' in folder_data:
        for subfolder_id in folder_data['subFolders']:
            subfolder = get_folder_hierarchy( subfolder_id , displayFileId , displayFolderId)
            if subfolder:
                hierarchy['children'].append(subfolder)
    
    return hierarchy

def get_folder_hierarchy_names_only(folder_id):
    """
    Retrieve the folder hierarchy with only names for a given folder ID.

    This function fetches the folder document from the database using the provided folder ID,
    and constructs a hierarchical structure containing only the names of the folders and files.
    It recursively processes subfolders to build the complete hierarchy.

    Args:
        folder_id (str): The unique identifier of the folder to retrieve the hierarchy for.

    Returns:
        Dict[str, Any]: A dictionary representing the folder hierarchy with names only.
                        Returns None if the folder does not exist.
    """
    folder_ref = db.collection('folders').document(folder_id)
    folder_doc = folder_ref.get()
    
    if not folder_doc.exists:
        return None
    
    folder_data = folder_doc.to_dict()
    hierarchy = {
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
                hierarchy['files'].append(file_data.get('name', ''))
    
    # Recursively get subfolders
    if 'subFolders' in folder_data:
        for subfolder_id in folder_data['subFolders']:
            subfolder = get_folder_hierarchy_names_only( subfolder_id)
            if subfolder:
                hierarchy['children'].append(subfolder)
    return hierarchy

def optimize_hierarchy(folder_id):
    """
    Optimize the folder hierarchy using an AI model.

    This function retrieves the current folder hierarchy, sends it to an AI model for optimization,
    and processes the returned JSON structure to extract the optimized hierarchy and its description.

    Args:
        folder_id (str): The unique identifier of the folder to optimize.

    Returns:
        Tuple[Dict[str, Any], str]: A tuple containing the optimized folder hierarchy as a dictionary
                                    and a description of the AI's optimization.

    Raises:
        ValueError: If the AI model's response does not contain valid JSON.
    """
    # Building and sending the prompt
    folder_hierarchy = json.dumps(get_folder_hierarchy_names_only(folder_id))
    llm_prompt = PROMPT_TEMPLATE.format_messages(
        current_structure = folder_hierarchy
    )
    llm_result = MODEL.invoke(llm_prompt)
    
    # Handling the JSON (langchain offers some way to structure the JSON so this will likely change)
    start = llm_result.content.index('{')
    end = llm_result.content.rindex('}') + 1
    json_str = llm_result.content[start:end]
    ai_description= ast.literal_eval((llm_result.content.replace('```json\n', '').replace('\n```', '')))[1]
    return json.loads(json_str),ai_description



def generateFileMap(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a map of file names to their corresponding IDs from a hierarchical file structure.

    This function traverses a nested dictionary representing a file hierarchy,
    and creates a mapping where each file name is associated with a list of its IDs.

    Args:
        structure (Dict[str, Any]): The hierarchical structure of files and directories.

    Returns:
        Dict[str, Any]: A dictionary mapping file names to lists of their IDs.
    """
    file_map = defaultdict(list)

    def traverse(node: Dict[str, Any]):
        for file in node.get('files', []):
            file_map[file['name']].append(file['id'])
        
        for child in node.get('children', []):
            traverse(child)

    traverse(structure)
    return file_map

def generateSubFoldersMap(current_folder: Folder) -> Dict[str, Any]:
    """
    Generate a map of subfolder names to their corresponding Folder objects.

    This function iterates through the subfolders of the given folder and creates
    a dictionary where each subfolder name is associated with its Folder object.

    Args:
        current_folder (Folder): The folder whose subfolders are to be mapped.

    Returns:
        Dict[str, Any]: A dictionary mapping subfolder names to their Folder objects.
    """
    return {subfolder.name: subfolder for subfolder in current_folder.getSubfolders()}

def update_folder_structure_batched(root_folder: Folder, ai_structure: Dict[str, Any], initial_structure: Dict[str, Any]) -> Folder:
    """
    Update the folder structure in a batched manner based on AI-generated and initial structures.

    This function updates the folder hierarchy by comparing the AI-generated structure with the initial structure.
    It processes the folders and files in batches to optimize database operations and ensure consistency.

    Args:
        root_folder (Folder): The root folder to start the update from.
        ai_structure (Dict[str, Any]): The AI-generated folder structure.
        initial_structure (Dict[str, Any]): The initial folder structure.

    Returns:
        Folder: The updated root folder.

    Raises:
        Exception: If the number of files exceeds the maximum allowed or if the maximum depth is reached.
    """
    batch = db.batch()
    file_map = generateFileMap(initial_structure)
    processed_folders = set()

    numberOffiles = 0
    for file_list in file_map.values():
        numberOffiles += len(file_list)
    
    if numberOffiles > MAX_FILES:
        raise Exception(f"Too many files to process in the hierarchy suggestion. Maximum number of files allowed is {MAX_FILES}")

    def update_structure(structure: Dict[str, Any], current_folder: Folder, depth: int = 0):

        print(current_folder.to_dict())
        if depth > MAX_DEPTH:
            print(f"Warning: Maximum depth reached at folder {current_folder.id}")
            raise Exception("Maximum depth reached when updated hierarchy ")

        if current_folder.id in processed_folders:
            print(f"Warning: Folder {current_folder.id} has already been processed. Skipping to avoid loop.")
            return

        processed_folders.add(current_folder.id)
        existing_subfolders = generateSubFoldersMap(current_folder)
        subfolders_to_keep = set()

        for child in structure.get('children', []):
            if child['name'] in existing_subfolders:
                subfolder = existing_subfolders[child['name']]
                update_structure(child, subfolder, depth + 1)
                subfolders_to_keep.add(subfolder.id)
            else:
                subfolder = current_folder.createSubFolderTransactional(child['name'], batch)
                update_structure(child, subfolder, depth + 1)
                subfolders_to_keep.add(subfolder.id)

        for subfolder in existing_subfolders.values():
            if subfolder.id not in subfolders_to_keep:
                delete_folder_recursively(subfolder, batch, depth + 1)

        current_folder.files = []

        for file in structure.get('files', []):
            file_name = file['name'] if isinstance(file, dict) else file
            
            if file_name in file_map and file_map[file_name]:
                file_id = file_map[file_name].pop(0)
                if not file_map[file_name]:
                    del file_map[file_name]
            else:
                raise Exception(f"File {file_name} not found in initial structure")

            current_folder.createFileTransactional(file_id,batch)

        batch.set(db.collection('folders').document(current_folder.id), current_folder.to_dict())

    def delete_folder_recursively(folder: Folder, batch, depth: int = 0):
        if depth > MAX_DEPTH:
            print(f"Warning: Maximum depth reached while deleting folder {folder.id}")
            return

        for subfolder in folder.getSubfolders():
            delete_folder_recursively(subfolder, batch, depth + 1)
        
        for file_id in folder.files:
            batch.delete(db.collection('files').document(file_id))
        
        batch.delete(db.collection('folders').document(folder.id))

    update_structure(ai_structure, root_folder)

    # Check if there are unused files

    isUnused = False
    for file_list in file_map.values():
        if file_list:
            isUnused = True
    if isUnused:
        unused_files = [f for files in file_map.values() for f in files]
        for file_id in unused_files:
            root_folder.createFileTransactional(file_id,batch)

    # Commit the batch
    batch.commit()

    return root_folder