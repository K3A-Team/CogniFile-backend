from fastapi import APIRouter, status, Depends
from Core.Shared.Database import Database, db
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from starlette.responses import JSONResponse
from fastapi import UploadFile
from fastapi import File
import uuid
from Models.Entities.StorageFile import StorageFile
from Models.Entities.Folder import Folder
from Core.Shared.Utils import storeInStorageHandler




async def createFileHandler(userID:str, folderId: str , file: UploadFile = File(...) ):
    """
    Creates a file in the specified folder and stores it in Firebase Storage.

    Args:
        userID (str): The ID of the user creating the file.
        folderId (str): The ID of the folder where the file will be stored.
        file (UploadFile): The file to be uploaded.

    Returns:
        dict: The created file's data.

    Raises:
        Exception: If the folder ID is not specified, the folder does not exist, or the user does not have write permissions.
    """
    parentFolder = None
    readId = []
    writeId = []

    if folderId is None:
        raise Exception("You must specify a folder to store the file in")
    
    parentFolder = await Database.getFolder(folderId)

    if parentFolder is None:
        raise Exception("File creation in non-existing folder")

    if ((userID != parentFolder["ownerId"]) and (userID not in parentFolder["writeId"])):
        raise Exception("You are not allowed to create a folder in this directory")
    readId = parentFolder["readId"]
    writeId = parentFolder["writeId"]
    name = file.filename
    url = await storeInStorageHandler(file)
        
    fileObj = StorageFile(
        name=name,
        ownerId=userID,
        folder=folderId,
        readId=readId,
        writeId=writeId,
        url=url
    )
    
    #update parent folder
    parentFolder["files"].append(fileObj.id)
    await Database.edit("folders", folderId, parentFolder)

    fileDict = await Database.createFile(fileObj)
    return fileDict

async def getFileHandler(userID:str, fileID: str):
    """
    Retrieves a file's data if the user has access permissions.

    Args:
        userID (str): The ID of the user requesting the file.
        fileID (str): The ID of the file to be retrieved.

    Returns:
        dict: The requested file's data.

    Raises:
        Exception: If the user does not have read or write permissions for the file.
    """
    file = await Database.getFile(fileID=fileID)
    if ((userID != file["ownerId"]) and (userID not in file["readId"]) and (userID not in file["writeId"])):
        raise Exception("You are not allowed to access this directory")
    else:
        return file