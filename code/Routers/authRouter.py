from fastapi import APIRouter, status
from Models.Requests.AuthRequestsModels import RegisterRequest, LoginRequest
from starlette.responses import JSONResponse
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import *
from Core.Shared.Security import *
from handlers.authHandlers import registerUserHandler , loginUserHandler

authRouter = APIRouter()

@authRouter.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: RegisterRequest):
    """
    Registers a new user and returns a JSON response with user details and a JWT token.
    """
    try:
        data = request.dict()
        userDict = await registerUserHandler(            
            data["firstName"], 
            data["lastName"],
            data["email"],
            data["password"]
        )
        jwtToken = userDict["token"]
        del userDict["token"]

        response = JSONResponse(
            content={"success": True, "user": userDict, "token": jwtToken},
            headers={"Authorization": f"Bearer {jwtToken}"},
        )

        return response

    except Exception as e:
        return {"success": False, "message": str(e)}


@authRouter.post("/login", status_code=status.HTTP_201_CREATED)
async def login_user(request: LoginRequest):
    """
    Authenticates a user and returns a JSON response with user details and a JWT token.
    """
    try:
        data = request.dict()

        user  = await loginUserHandler(data["email"], data["password"])
        jwtToken = user["token"]
        del user["token"]

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
