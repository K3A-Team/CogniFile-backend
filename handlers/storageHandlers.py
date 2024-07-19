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


async def storeInStorageHandler(userID:str, file: UploadFile = File(...)):

        time = int(datetime.now().timestamp())
        fileID = str(time) + file.filename
        file.filename = fileID
        f = file.file
        url = Storage.store(f, fileID)
        
        return url

