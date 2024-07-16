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


load_dotenv()



storageRouter = APIRouter()


@storageRouter.post("/", status_code=status.HTTP_201_CREATED)
async def storeInStorage(
        file: UploadFile = File(...),
        userID: str = Depends(statusProtected)):
    try:
        time = int(datetime.now().timestamp())
        fileID = str(time) + file.filename
        file.filename = fileID
        f = file.file
        url = Storage.store(f, fileID)
        
        return {"success": True, "url": url}
    except Exception as e:
        return {"success": False, "message": str(e)}
