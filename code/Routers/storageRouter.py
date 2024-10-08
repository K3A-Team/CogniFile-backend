from fastapi import APIRouter, Depends
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import LoginProtected
from Routers.foldersRouter import foldersRouter
from Routers.filesRouter import filesRouter
from Routers.sharedStorageRouter import sharedStorageRouter
from handlers.storageHandlers.storageHandlers import get_shared_content_handler
from handlers.storageHandlers.storageHandlers import getRecentElementsHandler , removeTrashHandler
from handlers.storageHandlers.foldersHandlers import restoreFileHandler , restoreFolderHandler

# Create a new APIRouter instance for storage-related routes
storageRouter = APIRouter()

@storageRouter.get("/sharedContent")
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
    
@storageRouter.delete("/trash")
async def deleteTrash(userID: str = Depends(LoginProtected)):
    """
    Deletes all the files and folders in the trash.
    """
    try:
        trash = await removeTrashHandler(userID)
        return {"success": True, "trash": trash}

    except Exception as e:
        return {"success": False, "message": str(e)}

@storageRouter.get("/restore/file/{fileId}", status_code=status.HTTP_200_OK)
async def restoreFile(fileId: str, userID: str = Depends(LoginProtected)):
    """
    Restores the specified file.
    """
    try:

        folderDict = await restoreFileHandler(userID=userID, fileId=fileId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}
    
@storageRouter.get("/restore/folder/{folderId}", status_code=status.HTTP_200_OK)
async def restoreFolder(folderId: str, userID: str = Depends(LoginProtected)):
    """
    Restores the specified folder.
    """
    try:

        folderDict = await restoreFolderHandler(userId=userID, folderId=folderId)

        return {"success": True, "folder": folderDict}

    except Exception as e:
        return {"success": False, "message": str(e)}


# Nest foldersRouter and filesRouter inside storageRouter
storageRouter.include_router(foldersRouter, tags=["folders"], prefix="/folder")

# Nest filesRouter inside storageRouter with the prefix "/folders" and tag "files"
storageRouter.include_router(filesRouter, tags=["files"], prefix="/file")

# Nest sharedStorageRouter inside storageRouter with the prefix "/shared" and tag "shared"
storageRouter.include_router(sharedStorageRouter, tags=["shared"], prefix="/shared")
