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
from handlers.storageHandlers.filesHandlers import createFileHandler , getFileHandler


load_dotenv()



filesRouter = APIRouter()


@filesRouter.post("/{folderId}/file", status_code=status.HTTP_201_CREATED)
async def createFile(
        folderId: str,
        file : UploadFile = File(...),
        userID: str = Depends(statusProtected)):
    #try:
    parentFolderID = folderId

    folderDict = await createFileHandler(userID=userID,folderId=parentFolderID, file=file)

    return {"success": True, "file": folderDict}

    #except Exception as e:
    #    return {"success": False, "message": str(e)}
    
@filesRouter.get("/file/{fileId}", status_code=status.HTTP_200_OK)
async def getFile(fileId : str ,userID: str = Depends(statusProtected)):
    try:

        folderDict = await getFileHandler(userID=userID, fileID=fileId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}
    

