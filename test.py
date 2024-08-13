from typing import Dict, Any
import uuid
from Models.Entities.Folder import Folder
from collections import defaultdict
from Core.Shared.Database import db
from services.fileHierarchyService import get_folder_hierarchy , optimize_hierarchy

def generateFileMap(initial_structure: Dict[str, Any]) -> Dict[str, Any]:
    file_map = defaultdict(list)
    for file in initial_structure['files']:
        file_map[file['name']].append(file['id'])
    return file_map

def generateSubFoldersMap(current_folder : Folder) -> Dict[str, Any]:
    return {subfolder.name: subfolder for subfolder in current_folder.getSubfolders()}

def update_folder_structure(root_folder: Folder, ai_structure: Dict[str, Any], initial_structure: Dict[str, Any]) -> Folder:
    file_map = generateFileMap(initial_structure)

    processed_folders = set()

    def update_structure(structure: Dict[str, Any], current_folder: Folder):
        processed_folders.add(current_folder.id)
        existing_subfolders = generateSubFoldersMap(current_folder)
        subfolders_to_keep = set()


        for child in structure.get('children', []):
            if child['name'] in existing_subfolders:
                subfolder = existing_subfolders[child['name']]
                update_structure(child, subfolder)
                subfolders_to_keep.add(subfolder.id)
            else:

                subfolder_id = current_folder.createSubFolder(child['name'])
                new_subfolder = Folder.loadWithId(subfolder_id)
                update_structure(child, new_subfolder)
                subfolders_to_keep.add(subfolder_id)

        for subfolder in existing_subfolders.values():
            if subfolder.id not in subfolders_to_keep:
                delete_folder_recursively(subfolder)

        current_folder.files = []

        for file in structure.get('files', []):
            file_name = file['name'] if isinstance(file, dict) else file
            
            if file_name in file_map and file_map[file_name]:
                file_id = file_map[file_name].pop(0)
                if not file_map[file_name]:
                    del file_map[file_name]
            else:
                file_id = str(uuid.uuid4())
                db.collection('files').document(file_id).set({
                    'id': file_id,
                    'name': file_name,
                    'ownerId': current_folder.ownerId,
                    'parent': current_folder.id
                })

            current_folder.createFile(file_id)

        db.collection('folders').document(current_folder.id).set(current_folder.to_dict())

    def delete_folder_recursively(folder: Folder):
        for subfolder in folder.getSubfolders():
            delete_folder_recursively(subfolder)
        
        for file_id in folder.files:
            db.collection('files').document(file_id).delete()
        
        db.collection('folders').document(folder.id).delete()


    update_structure(ai_structure, root_folder)


    unused_files = [f for files in file_map.values() for f in files]
    for file_id in unused_files:
        root_folder.createFile(file_id)

    return root_folder



ai_structure = optimize_hierarchy("5084ff73-6caf-494d-889f-e689302d26e7")

initial_structure = get_folder_hierarchy("5084ff73-6caf-494d-889f-e689302d26e7",displayFileId=True)


rootFolder = Folder.loadWithId("5084ff73-6caf-494d-889f-e689302d26e7")



updated_folder = update_folder_structure(rootFolder, ai_structure, initial_structure)



print(get_folder_hierarchy("5084ff73-6caf-494d-889f-e689302d26e7"))