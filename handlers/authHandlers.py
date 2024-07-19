from fastapi import APIRouter, status, Depends
from Models.Requests.AuthRequestsModels import RegisterRequest, LoginRequest
from Core.Shared.Database import Database, db
from Core.Shared.Storage import Storage
from Core.Shared import Security
from starlette.responses import JSONResponse
from Core.Shared.ErrorResponses import *
from datetime import datetime
from Middlewares.authProtectionMiddlewares import *
from fastapi import UploadFile
from fastapi import File
from dotenv import load_dotenv
from Core.Shared.Security import *
import uuid
from Models.Entities.User import User
from handlers.storageHandlers.foldersHandlers import createFolderHandler

async def registerUserHandler(firstname : str, lastname : str, email : str, password : str):


    email = email.lower()

    result = db.collection("users").where(
        "email", "==", email).get()

    if len(result) > 0:
        raise Exception("User already exists")
    
    userId = str(uuid.uuid4())

    rootFolder = await createFolderHandler(userID=userId, folderName="/")

    rootFolderId = rootFolder["id"]
    
    user = User(
        id=userId,
        firstName=firstname, 
        lastName=lastname, 
        email=email, 
        password=hashPassword(password),
        rootFolderId=rootFolderId
        )

    userDict = user.to_dict()

    await Database.store("users", user.id, userDict)
    

    del userDict["password"]

    jwtToken = createJwtToken({"id": userDict["id"]})

    del userDict["id"]

    userDict["token"] = jwtToken

    return userDict

async def loginUserHandler(email,password):

    email = email.lower()

    result = db.collection("users").where(
        "email", "==", email).get()

    if len(result) == 0:
        raise Exception("Email does not exist")
    user = result[0].to_dict()

    if user["password"] == hashPassword(password):
        del user["password"]

        jwtToken = createJwtToken({"id": user["id"]})

        del user["id"]

        user["token"] = jwtToken

        return user

    else:
        raise Exception("Invalid credentials")
