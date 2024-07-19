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
from handlers.storageHandlers.foldersHandlers import storeInStorageHandler 
from Models.Requests.FolderRequestsModels import CreateFolderRequest
from handlers.storageHandlers.foldersHandlers import createFolderHandler , getFolderHandler


load_dotenv()



foldersRouter = APIRouter()


@foldersRouter.post("/{folderId}/folder", status_code=status.HTTP_201_CREATED)
async def createSubFodler(
        ceateFolderRequest: CreateFolderRequest,
        folderId: str,
        userID: str = Depends(statusProtected)):
    try:
        request = ceateFolderRequest.dict()
        folderName = request["folderName"]
        parentFolderID = folderId

        folderDict = await createFolderHandler(userID=userID, folderName=folderName, parentFolderID=parentFolderID)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}
    
@foldersRouter.get("/{folderId}", status_code=status.HTTP_201_CREATED)
async def getFolder(folderId : str ,userID: str = Depends(statusProtected)):
    try:

        folderDict = await getFolderHandler(userID=userID, folderID=folderId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}
    

