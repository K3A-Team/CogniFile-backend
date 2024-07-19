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
from Routers.foldersRouter import foldersRouter
from Routers.filesRouter import filesRouter


load_dotenv()



storageRouter = APIRouter()
# Nest foldersRouter and filesRouter inside storageRouter
storageRouter.include_router(foldersRouter, tags=["folders"], prefix="/folders")
storageRouter.include_router(filesRouter, tags=["files"], prefix="/folders")

@storageRouter.post("/", status_code=status.HTTP_201_CREATED)
async def storeInStorage(
        file: UploadFile = File(...),
        userID: str = Depends(statusProtected)):
    try:
        url = await storeInStorageHandler(userID, file)
        return {"success": True, "url": url}
    except Exception as e:
        return {"success": False, "message": str(e)}

