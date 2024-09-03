from fastapi import APIRouter, status, Depends, Form
from Middlewares.authProtectionMiddlewares import LoginProtected
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from fastapi import UploadFile
from fastapi import File
from dotenv import load_dotenv
from Models.Requests.FolderRequestsModels import CreateFolderRequest
from handlers.storageHandlers.foldersHandlers import createFolderHandler , getFolderHandler ,deleteFolderHandler
from handlers.storageHandlers.filesHandlers import createFileHandler 

load_dotenv()

foldersRouter = APIRouter()

@foldersRouter.post("/{folderId}/folder", status_code=status.HTTP_201_CREATED)
async def createSubFodler(
        createFolderRequest: CreateFolderRequest,
        folderId: str,
        userID: str = Depends(LoginProtected)):
    """
    Creates a subfolder within the specified folder; the logic is handled inside the handler.
    """
    try:
        request = createFolderRequest.dict()
        folderName = request["folderName"]
        parentFolderID = folderId

        folderDict = await createFolderHandler(userID=userID, folderName=folderName, parentFolderID=parentFolderID)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}

@foldersRouter.get("/{folderId}", status_code=status.HTTP_200_OK)
async def getFolder(folderId : str, userID: str = Depends(LoginProtected)):
    """
    Retrieves the details of the specified folder; the logic is handled inside the handler.
    """
    try:

        folderDict = await getFolderHandler(userID=userID, folderID=folderId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}
    
@foldersRouter.delete("/{folderId}", status_code=status.HTTP_200_OK)
async def removeFolder(folderId : str, userID: str = Depends(LoginProtected)):
    """
    Removes the specified folder; the logic is handled inside the handler.
    """
    try:

        folderDict = await deleteFolderHandler(userId=userID, fodlerId=folderId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}
    

@foldersRouter.post("/{folderId}/file", status_code=status.HTTP_201_CREATED)
async def createFile(
        folderId: str,
        file : UploadFile = File(...),
        force: bool | None = Form(None),
        userID: str = Depends(LoginProtected)):
    """
    Uploads a new file to the specified folder and returns the file details.
    """
    try:
        parentFolderID = folderId
        folderDict = await createFileHandler(userID=userID,folderId=parentFolderID, file=file, force=force)

        return {"success": True, "file": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}