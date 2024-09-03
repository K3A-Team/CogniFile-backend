from Core.Shared.Database import Database , db
from firebase_admin import firestore
from Models.Entities.Folder import Folder
from Models.Entities.StorageFile import StorageFile
from typing import List


def get_shared_content_handler(searchQuery: str, userID: str):
    """
    Retrieves the shared content (files and folders) that match the search query.
    Shared content includes:
    - Files and folders where the user is the owner and there is at least one readId or writeId.
    - Files and folders where the user is included in the readId or writeId.
    """
    try:

        refs = Database.setupRefs(["files", "folders"])
        files_ref = refs["files"]
        folders_ref = refs["folders"]

        owned_shared_files_r = [doc.to_dict() for doc in files_ref.where("ownerId", "==", userID).where("readId", "!=", []).stream()]
        owned_shared_files_w = [
            doc.to_dict() for doc in files_ref.where("ownerId", "==", userID).where("writeId", "!=", []).stream()
            if doc.id not in {item['id'] for item in owned_shared_files_r}
        ]
        shared_files_r = [doc.to_dict() for doc in files_ref.where("readId", "array_contains", userID).stream()]
        shared_files_w = [
            doc.to_dict() for doc in files_ref.where("writeId", "array_contains", userID).stream()
            if doc.id not in {item['id'] for item in shared_files_r}
        ]
        
        owned_shared_folders_r = [doc.to_dict() for doc in folders_ref.where("ownerId", "==", userID).where("readId", "!=", []).stream()]
        owned_shared_folders_w = [
            doc.to_dict() for doc in folders_ref.where("ownerId", "==", userID).where("writeId", "!=", []).stream()
            if doc.id not in {item['id'] for item in owned_shared_folders_r}
        ]
        shared_folders_r = [doc.to_dict() for doc in folders_ref.where("readId", "array_contains", userID).stream()]
        shared_folders_w = [
            doc.to_dict() for doc in folders_ref.where("writeId", "array_contains", userID).stream()
            if doc.id not in {item['id'] for item in shared_folders_r}
        ]

        all_shared_files = owned_shared_files_r + owned_shared_files_w + shared_files_r + shared_files_w
        all_shared_folders = owned_shared_folders_r + owned_shared_folders_w + shared_folders_r + shared_folders_w

        if searchQuery:

            all_user_ids = set()
            for item in all_shared_files + all_shared_folders:
                all_user_ids.update(item.get('readId', []))
                all_user_ids.update(item.get('writeId', []))
                all_user_ids.add(item.get('ownerId', ''))

            user_names_map = Database.get_user_names_map(list(all_user_ids))

            searchQuery = searchQuery.lower()

            all_shared_files = [
                item for item in all_shared_files
                if (
                    searchQuery in item.get('name', '').lower() or
                    any(searchQuery in tag.lower() for tag in item.get('tags', [])) or
                    Database.matches_search_term(item, searchQuery, user_names_map, userID)
                )
            ]

            all_shared_folders = [
                item for item in all_shared_folders
                if (
                    searchQuery in item.get('name', '').lower() or
                    Database.matches_search_term(item, searchQuery, user_names_map, userID)
                )
            ]

        return {
            "files": all_shared_files,
            "folders": all_shared_folders
        }

    except Exception as e:
        raise Exception(str(e))


def getRecentElementsHandler(userId,MAX_ITEMS=10):
    try:

        items = []

        folders_ref = db.collection('folders')
        query = folders_ref.where('ownerId', '==', userId) \
                .order_by('interactionDate', direction=firestore.Query.DESCENDING )\
                .limit(MAX_ITEMS)
        results = query.stream()


        for folder in results:
            folderDict = folder.to_dict()
            folderDict['type'] = 'folder'
            items.append(folderDict)


        files_ref = db.collection('files')
        query = files_ref.where('ownerId', '==', userId) \
                .order_by('interactionDate', direction=firestore.Query.DESCENDING )\
                .limit(MAX_ITEMS)

        results = query.stream()

        for file in results:
            fileDict = file.to_dict()
            fileDict['type'] = 'file'
            items.append(fileDict)

        # Trier les items par date d'interaction

        items.sort(key=lambda x: x['interactionDate'], reverse=True)

        # Récupérer les 10 premiers

        items = items[:10]

        for index, item in enumerate(items):
            if item['type'] == 'folder':
                # Update the folder item with new structure
                items[index] = {
                    'name': item.get('name'),
                    'size': '0 Mb',
                    'children': len(item.get('subFolders', [])) + len(item.get('files', [])),
                    'interactionDate': item.get('interactionDate'),
                    'type': 'folder'
                }
            elif item['type'] == 'file':
                # Update the file item with new structure
                items[index] = {
                    'name': item.get('name'),
                    'size': item.get('size'),
                    'url': item.get('url'),
                    'interactionDate': item.get('interactionDate'),
                    'type': 'file'
                }

        return items

    except Exception as e:
        raise Exception(str(e))
    
async def removeTrashHandler(userId: str):
    """
    Removes all files and folders in the Trash folder of the user.
    """
    try:
        user =await Database.getUser(userId)
        # Get the Trash folder of the user
        folder = await Folder.loadWithId(user.trashFolderId)
        # Delete all files and folders in the Trash folder
        batch = db.batch()

        # Recursively delete all files and folders in the Trash folder
        for subfolder in folder.getSubfolders():
            delete_folder_recursively(subfolder, batch)
        for file_id in folder.files:
            batch.delete(db.collection('files').document(file_id))

        # Commit the batched writes
        batch.commit()


        return {
            'success': True
        }

    except Exception as e:
        raise Exception(str(e))



MAX_DEPTH = 50
def delete_folder_recursively(folder: Folder, batch, depth: int = 0):
        if depth > MAX_DEPTH:
            print(f"Warning: Maximum depth reached while deleting folder {folder.id}")
            return

        for subfolder in folder.getSubfolders():
            delete_folder_recursively(subfolder, batch, depth + 1)
        
        for file_id in folder.files:
            batch.delete(db.collection('files').document(file_id))
        
        batch.delete(db.collection('folders').document(folder.id))