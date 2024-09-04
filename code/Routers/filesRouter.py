from fastapi import APIRouter, status, Depends
from Middlewares.authProtectionMiddlewares import LoginProtected
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from dotenv import load_dotenv
from handlers.storageHandlers.filesHandlers import  getFileHandler
from handlers.storageHandlers.filesHandlers import  deleteFileHandler

load_dotenv()

filesRouter = APIRouter()

@filesRouter.get("/{fileId}", status_code=status.HTTP_200_OK)
async def getFile(fileId : str ,userID: str = Depends(LoginProtected)):
    """
    Retrieves the details of a specified file.
    """
    try:

        folderDict = await getFileHandler(userID=userID, fileID=fileId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}
    
@filesRouter.delete("/{fileId}", status_code=status.HTTP_200_OK)
async def removeFile(fileId : str, userID: str = Depends(LoginProtected)):
    """
    Removes the specified file.
    """
    try:

        folderDict = await deleteFileHandler(userID=userID, fileID=fileId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}


