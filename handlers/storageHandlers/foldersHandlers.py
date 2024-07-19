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


async def storeInStorageHandler(userID:str, file: UploadFile = File(...)):

        time = int(datetime.now().timestamp())
        fileID = str(time) + file.filename
        file.filename = fileID
        f = file.file
        url = Storage.store(f, fileID)
        
        return url

async def createFolderHandler(userID:str, folderName: str , parentFolderID: str = None):
    parentFolder = None
    readId = []
    writeId = []
    if parentFolderID is not None:
        parentFolder = await Database.getFolder(parentFolderID)
        if ((userID != parentFolder["ownerId"]) and (userID not in parentFolder["readId"]) and (userID not in parentFolder["writeId"])):
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
    folder = await Database.getFolder(folderID)
    if ((userID != folder["ownerId"]) and (userID not in folder["readId"]) and (userID not in folder["writeId"])):
        raise Exception("You are not allowed to access this directory")
    else:
        return folder