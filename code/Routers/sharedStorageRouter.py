from fastapi import APIRouter, Depends
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import LoginProtected
from handlers.sharedStorageHandlers import getSharedStorage , createSharedStorage , getUserSharedStorages


# Create a new APIRouter instance for storage-related routes
sharedStorageRouter = APIRouter()

@sharedStorageRouter.get("/")
async def getUserSharedStorages( userID: str = Depends(LoginProtected)):
    try:
        sharedContent = await getUserSharedStorages(userID)
        return {
            "success": True,
            "content": sharedContent
            }
    except Exception as e:
        return {"success": False, "message": str(e)}
    
@sharedStorageRouter.post("/")
async def createSharedStorageRoute( storageName , image: UploadFile = File(...), userId : str = Depends(LoginProtected),):
    try:
        storageId = await createSharedStorage(userId , storageName , image)
        return {
            "success": True,
            "storageId": storageId
            }
    except Exception as e:
        return {"success": False, "message": str(e)}