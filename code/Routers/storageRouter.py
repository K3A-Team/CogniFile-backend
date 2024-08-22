from fastapi import APIRouter, Depends
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import LoginProtected
from Routers.foldersRouter import foldersRouter
from Routers.filesRouter import filesRouter
from handlers.storageHandlers.storageHandlers import get_shared_content_handler
from handlers.storageHandlers.storageHandlers import getRecentElementsHandler

# Create a new APIRouter instance for storage-related routes
storageRouter = APIRouter()

@storageRouter.get("/shared")
def getSharedContent(search: str = None, userID: str = Depends(LoginProtected)):
    """
    Retrieves the shared content (files and folders) that match the search query (if exists).
    """
    try:
        result = get_shared_content_handler(search, userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
    
@storageRouter.get("/recent")
def getRecentElements(userID: str = Depends(LoginProtected)):
    """
    Retrieves the recent files and folders.
    """
    try:
        result = getRecentElementsHandler(userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
    


# Nest foldersRouter and filesRouter inside storageRouter
storageRouter.include_router(foldersRouter, tags=["folders"], prefix="/folder")

# Nest filesRouter inside storageRouter with the prefix "/folders" and tag "files"
storageRouter.include_router(filesRouter, tags=["files"], prefix="/file")
