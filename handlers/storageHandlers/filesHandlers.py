from fastapi import APIRouter, status, Depends
from Middlewares.authProtectionMiddlewares import statusProtected
from Core.Shared.Database import Database, db
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from starlette.responses import JSONResponse
from fastapi import UploadFile
from fastapi import File
import uuid
from dotenv import load_dotenv
import os
from Models.Entities.StorageFile import StorageFile
from Models.Entities.Folder import Folder


load_dotenv()


async def storeInStorageHandler(file: UploadFile = File(...)):

        time = int(datetime.now().timestamp())
        fileID = str(time) + file.filename
        file.filename = fileID
        f = file.file
        url = Storage.store(f, fileID)
        
        return url

async def createFileHandler(userID:str, folderId: str , file: UploadFile = File(...) ):
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
    file = await Database.getFile(fileID=fileID)
    if ((userID != file["ownerId"]) and (userID not in file["readId"]) and (userID not in file["writeId"])):
        raise Exception("You are not allowed to access this directory")
    else:
        return file