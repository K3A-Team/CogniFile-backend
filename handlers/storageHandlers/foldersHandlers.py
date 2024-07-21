from fastapi import APIRouter, status, Depends
from Core.Shared.Database import Database, db
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from fastapi import File
import uuid
from Models.Entities.StorageFile import StorageFile
from Models.Entities.Folder import Folder



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

async def getFolderHandler(userID:str, folderID: str):
    """
    Retrieves a folder's data if the user has access permissions.

    Args:
        userID (str): The ID of the user requesting the folder.
        folderID (str): The ID of the folder to be retrieved.

    Returns:
        dict: The requested folder's data.

    Raises:
        Exception: If the user does not have read or write permissions for the folder.
    """
    folder = await Database.getFolder(folderID)
    if ((userID != folder["ownerId"]) and (userID not in folder["readId"]) and (userID not in folder["writeId"])):
        raise Exception("You are not allowed to access this directory")
    else:
        return folder