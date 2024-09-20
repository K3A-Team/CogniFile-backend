from Core.Shared.Database import Database , db
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from Models.Entities.Folder import Folder
from typing import List
from handlers.storageHandlers.filesHandlers import createFileHandler
import datetime
from Core.Shared.Database import db

async def createFolderHandler(userID:str, folderName: str , parentFolderID: str = None):
    """
    Creates a new folder, optionally within a parent folder, and stores it in the database.

    Args:
        userID (str): The ID of the user creating the folder.
        folderName (str): The name of the new folder.
        parentFolderID (str, optional): The ID of the parent folder. Defaults to None.

    Returns:
        dict: The created folder's data.

    Raises:
        Exception: If the user does not have write permissions for the parent folder.
    """
    parentFolder = None
    readId = []
    writeId = []
    if parentFolderID is not None:
        parentFolder = await Database.getFolder(parentFolderID)
        if ((userID != parentFolder["ownerId"]) and (userID not in parentFolder["writeId"])):
            raise Exception("You are not allowed to create a folder in this directory")
        else:
            readId = parentFolder["readId"]
            writeId = parentFolder["writeId"]

    folder = Folder(name=folderName, ownerId=userID, parent=parentFolderID , readId=readId, writeId=writeId )
    # update the parent folder
    if parentFolder is not None:
        parentFolder["subFolders"].append(folder.id)
        await Database.edit("folders", parentFolderID, parentFolder)
    folderDict = await Database.createFolder(folder)
    return folderDict


async def createTrashFolderHandler(userID:str):
    """
    Creates a new trash folder for the user and stores it in the database.
    """
    readId = []
    writeId = []

    fodlerId = "Trash-" + str(uuid.uuid4())

    folder = Folder(name='Trash', ownerId=userID, parent=None , readId=readId, writeId=writeId , id = fodlerId)

    folderDict = await Database.createFolder(folder)
    return folderDict['id']

async def getFolderHandler(userID: str, folderID: str):
    """
    Retrieves a folder's data if the user has access permissions and filters based on the search term.

    Args:
        userID (str): The ID of the user requesting the folder.
        folderID (str): The ID of the folder to be retrieved.
        search (str): The search term to filter the files and folders.

    Returns:
        dict: The requested folder's data with all files and folders that match the search term, without hierarchy.

    Raises:
        Exception: If the user does not have read or write permissions for the folder.
    """
    folder = await Database.getFodlerFormatted(folderID)

    db.collection("folders").document(folderID).update({
        "interactionDate": datetime.datetime.now().isoformat()
    })

    if ((userID != folder["ownerId"]) and (userID not in folder["readId"]) and (userID not in folder["writeId"])):
        raise Exception("You are not allowed to access this directory")

    # get data about the subfolders and files 

    folder["interactionDate"] = datetime.datetime.now().isoformat()


    
    return folder


async def searchContentInFolderRecursive(folderID: str, searchTerm: str, userID: str):
    folder = await Database.read("folders", folderID)
    all_files = await Database.getFilesDetails(folder.get("files", []))
    all_sub_folders = await Database.getSubFoldersDetails(folder.get("subFolders", []))
    all_rw_users = await Database.getRWUsersDetails({
        "readId": folder.get("readId", []),
        "writeId": folder.get("writeId", [])
    }, ["id", "firstName", "lastName"])

    def contains_search_term(item):
        return searchTerm.lower() in item["name"].lower()

    matching_files = [
        file for file in all_files if (
            contains_search_term(file) or 
            any(
                searchTerm.lower() in user["firstName"].lower() or 
                searchTerm.lower() in user["lastName"].lower()
                for user in all_rw_users.get("readId", []) + all_rw_users.get("writeId", [])
            ) or 
            any(searchTerm.lower() in tag.lower() for tag in file.get("tags", []))
        )
    ]

    matching_sub_folders = [
        subFolder for subFolder in all_sub_folders if contains_search_term(subFolder) or any(
            searchTerm.lower() in user["firstName"].lower() or searchTerm.lower() in user["lastName"].lower()
            for user in all_rw_users.get("readId", []) + all_rw_users.get("writeId", [])
        )
    ]

    for subFolder in all_sub_folders:
        subFolderContent = await searchContentInFolderRecursive(subFolder["id"], searchTerm, userID)
        matching_files.extend(subFolderContent["files"])
        matching_sub_folders.extend(subFolderContent["subFolders"])

    matching_read_users = [
        user["id"] for user in all_rw_users.get("readId", [])
        if ((userID != user["id"]) and (searchTerm.lower() in user["firstName"].lower() or searchTerm.lower() in user["lastName"].lower()))
    ]
    matching_write_users = [
        user["id"] for user in all_rw_users.get("writeId", [])
        if ((userID != user["id"]) and (searchTerm.lower() in user["firstName"].lower() or searchTerm.lower() in user["lastName"].lower()))
    ]

    return {
        "files": matching_files,
        "subFolders": matching_sub_folders,
        "readId": matching_read_users if matching_read_users else all_rw_users.get("readId", []),
        "writeId": matching_write_users if matching_write_users else all_rw_users.get("writeId", []),
    }


async def deleteFolderHandler(userId , fodlerId):
    user = await Database.getUser(userId)
    folder = await Database.getFolder(fodlerId)

    if folder is None:
        raise Exception("Folder does not exist")
    parentFolderId = folder["parent"]
    if parentFolderId is None:
        raise Exception("You cannot delete a root or trash folder")
    parentFolder = await Database.getFolder(parentFolderId)

    if folder["ownerId"] != userId and userId not in folder["writeId"]:
        raise Exception("You are not allowed to delete this folder")
    
    trashFolderId = user["trashFolderId"]
    trashFolder = await Database.getFolder(trashFolderId)

    trashFolder["subFolders"].append(fodlerId)
    folder["parent"] = trashFolderId
    parentFolder["subFolders"].remove(fodlerId)

    await Database.edit("folders", trashFolderId, trashFolder)
    await Database.edit("folders", fodlerId, folder)
    await Database.edit("folders", parentFolderId, parentFolder)

    return folder


async def restoreFolderHandler(userId , folderId):
    user = await Database.getUser(userId)
    folder = await Database.getFolder(folderId)
    rootFolder = await Database.getFolder(user["rootFolderId"])

    if folder is None:
        raise Exception("Folder does not exist")
    
    parentFolderId = folder["parent"]
    if parentFolderId is None:
        raise Exception("You cannot restore a root or trash folder")
    
    parentFolder = await Database.getFolder(parentFolderId)

    folder["parent"] = rootFolder["id"]
    rootFolder["subFolders"].append(folderId)
    rootFolder["subFolders"] = list(set(rootFolder["subFolders"]))
    # Delete the folder from the children of the parent
    parentFolder["subFolders"].remove(folderId)

    await Database.edit("folders", folderId, folder)
    await Database.edit("folders", parentFolderId, parentFolder)
    await Database.edit("folders", user["rootFolderId"], rootFolder)

    return parentFolder

async def restoreFileHandler(userID:str,fileId: str):
    '''
    
    '''
    file = await Database.getFile(fileId)
    user = await Database.getUser(userID)
    if file is None:
        raise Exception("File does not exist")
    if ((userID != file["ownerId"])):
        raise Exception("You are not allowed to upload a file in this directory")
    folder = file["folder"]
    folder = await Database.getFolder(folder)
    folder["files"].remove(fileId)

    rootFolder = await Database.getFolder(user["rootFolderId"])
    
    rootFolder["files"].append(fileId)
    # remove all duplicates from the root folder files
    rootFolder["files"] = list(set(rootFolder["files"]))

    file["folder"] = user["rootFolderId"]
    await Database.edit("folders", folder["id"], folder)
    await Database.edit("folders", user["rootFolderId"], rootFolder)
    file = await Database.edit("files", file["id"], file)

    return folder

async def uploadFolderHandler(userID : str,files : List[UploadFile],folderId : str):
    folder_dict = {}
    parent_created = False
    for file in files:
        # Extract needed informations
        path_array = file.filename.split('/')
        file_name = path_array[-1]
        file_folder = path_array[-2]
        if (len(path_array) > 2):
            file_folder_parent_id = folder_dict[path_array[-3]]
        else:
            file_folder_parent_id = folderId
        # Get file folder or create if it doesn't exist
        if file_folder in folder_dict :
            file_folder_id = folder_dict[file_folder]
        else:
            folderDict = await createFolderHandler(userID=userID, folderName=file_folder, parentFolderID=file_folder_parent_id)
            file_folder_id = folderDict['id']
            folder_dict[file_folder] = file_folder_id
            if not parent_created : 
                created_folder_id = folderDict['id']
                parent_created = True
        # Create the file
        fileDict = await createFileHandler(userID=userID,folderId=file_folder_id, file=file, force=True,dir_name=file_name,valid_dir_name=True)   
    return await Database.getFodlerFormatted(created_folder_id)