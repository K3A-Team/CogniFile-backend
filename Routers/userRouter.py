from fastapi import APIRouter, status, Depends
from Middlewares.authProtectionMiddlewares import statusProtected
from Routers.storageRouter import storageRouter
from Core.Shared.ErrorResponses import *
from Core.Shared.Database import Database , db
from Core.Shared.Security import *
from Core.Shared.Storage import Storage
from Core.Shared.Utils import *
from starlette.responses import JSONResponse
from fastapi import File
from fastapi import UploadFile
import os
import uuid
import mimetypes
from dotenv import load_dotenv

load_dotenv()

TEMP_FILES_DIRECTORY = os.getenv("TEMP_FILES_DIRECTORY")

userRouter = APIRouter()


@userRouter.get("/profile", status_code=status.HTTP_201_CREATED)
async def getProfile(userID: str = Depends(statusProtected)):
    try:
        user = Database.read("users", userID)
        if user is None:
            return badRequestError("User not found")
        del user["password"]
        return {"success" : True, "user" : user}

    except Exception as e:
        return {"success" : False, "message" : str(e)}

@userRouter.put("/profile", status_code=status.HTTP_201_CREATED)
async def editProfile(request : dict,userID: str = Depends(statusProtected)):
    try:
        data = request
        user = {}
        if "firstName" in data:
            user["firstName"] = data["firstName"]
        if "lastName" in data:
            user["lastName"] = data["lastName"]
        if "email" in data:
            user["email"] = data["email"]
        if "password" in data:
            user["password"] = hashPassword(data["password"])
        
        if len(user) == 0:
            return badRequestError("No data to update")
        
        
        Database.edit("users", userID, user)
        return {"success" : True, "user" : user }

    except Exception as e:
        return {"success" : False, "message" : str(e)}

