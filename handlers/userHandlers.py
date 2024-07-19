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

async def getProfileHandler(userID: str):
    user = await Database.read("users", userID)
    if user is None:
        return badRequestError("User not found")
    del user["password"]
    return {"success" : True, "user" : user}

async def editProfileHandler(data : dict,userID: str):
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
    await Database.edit("users", userID, user)
    return user