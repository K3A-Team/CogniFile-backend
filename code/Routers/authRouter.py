from fastapi import APIRouter, status
from Models.Requests.AuthRequestsModels import RegisterRequest, LoginRequest, ResetPasswordRequest, ForgetPasswordRequest
from starlette.responses import JSONResponse
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import *
from Core.Shared.Security import *
from handlers.authHandlers import registerUserHandler , loginUserHandler, forgetPasswordHandler, resetPasswordHandler

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

@authRouter.post("/forget-password", status_code=status.HTTP_201_CREATED)
async def forget_password(request: ForgetPasswordRequest):
    """
    Sends a password reset email to the user.
    """
    try:
        data = request.dict()

        email = data["email"]

        if not email:
            return {"success": False, "message": "Email is required"}

        await forgetPasswordHandler(email)

        return {"success": True, "message": "Password reset email sent, if the email exists in our system, you will receive an email shortly."}

    except Exception as e:
        return {"success": False, "message": str(e)}

@authRouter.post("/reset-password", status_code=status.HTTP_201_CREATED)
async def reset_password(request: ResetPasswordRequest):
    """
    Resets a user's password.
    """
    try:
        data = request.dict()

        if not data["token"]:
            return {"success": False, "message": "Token is required"}
        
        if not data["new_password"]:
            return {"success": False, "message": "Password is required"}
        
        if not data["email"]:
            return {"success": False, "message": "Email is required"}

        response = await resetPasswordHandler(data)

        return {"success": True, "message": response["message"]}

    except Exception as e:
        return {"success": False, "message": str(e)}
