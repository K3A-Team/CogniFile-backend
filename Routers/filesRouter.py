from fastapi import APIRouter, status, Depends
from Middlewares.authProtectionMiddlewares import LoginProtected
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from dotenv import load_dotenv
from handlers.storageHandlers.filesHandlers import  getFileHandler

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


