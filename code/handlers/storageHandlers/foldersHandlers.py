from Core.Shared.Database import Database , db
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from Models.Entities.Folder import Folder
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
    parentFolderId = folder["parent"]
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
    
    