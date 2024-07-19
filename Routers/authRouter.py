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
from handlers.authHandlers import registerUserHandler , loginUserHandler

authRouter = APIRouter()


@authRouter.get("/")
def welcome():
    return "Router working"


@authRouter.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterRequest):
    try:
        data = request.dict()

        user = User(
            data["firstName"], 
            data["lastName"],
            data["email"],
            data["password"]
        )

        userDict = await registerUserHandler(user)


        jwtToken = userDict["token"]

        response = JSONResponse(
            content={"success": True, "user": userDict, "token": jwtToken},
            headers={"Authorization": f"Bearer {jwtToken}"},
        )

        return response

    except Exception as e:
       return {"success": False, "message": str(e)}


@authRouter.post("/login", status_code=status.HTTP_201_CREATED)
async def login_user(request: LoginRequest):
    try:
        data = request.dict()


        user  = await loginUserHandler(data["email"], data["password"])
        jwtToken = user["token"]

        response = JSONResponse(
            content={"success": True, "user": user, "token": jwtToken},
            headers={"Authorization": f"Bearer {jwtToken}"},
        )

        response.set_cookie(
            key="Authorization",
            value=jwtToken,
            httponly=True)
        return response

    except Exception as e:
        return {"success": False, "message": str(e)}
