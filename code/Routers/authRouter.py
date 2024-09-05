from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse
from Models.Requests.AuthRequestsModels import RegisterRequest, LoginRequest, ResetPasswordRequest, ForgetPasswordRequest
from starlette.responses import JSONResponse
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import *
from Core.Shared.Security import *
from Core.Shared.Database import Database
from services.SMTPService import send_welcome_email
from services.oAuthService import generate_server_session, get_github_user_info, get_google_user_info
from handlers.authHandlers import OAuthLoginHandler, registerUserHandler , loginUserHandler, forgetPasswordHandler, resetPasswordHandler

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

        await send_welcome_email(data["email"], f"{data['firstName']} {data['lastName']}")

        response = JSONResponse(
            content={"success": True, "user": userDict, "token": jwtToken},
            headers={"Authorization": f"Bearer {jwtToken}"},
        )

        return response

    except Exception as e:
        return {"success": False, "message": str(e)}


@authRouter.post("/login", status_code=status.HTTP_200_OK)
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

        if not data["token"] or not data["email"]:
            return {"success": False, "message": "Invalid reset link"}

        if not data["new_password"]:
            return {"success": False, "message": "Password is required"}

        response = await resetPasswordHandler(data)

        return {"success": True, "message": response["message"]}

    except Exception as e:
        return {"success": False, "message": str(e)}

@authRouter.get("/github")
def github_auth():
    authorization_url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={os.getenv('GITHUB_CLIENT_ID')}"
        f"&redirect_uri={os.getenv('GITHUB_REDIRECT_URI')}"
        "&scope=user:email"
    )
    return RedirectResponse(url=authorization_url)

@authRouter.get("/github/callback", include_in_schema=False)
async def github_callback(code: str):
    try:
        user_info = await get_github_user_info(code)

        if not user_info:
            return {"success": False, "message": "Failed to get user info from Github, try again later."}
        
        user = await OAuthLoginHandler(user_info)

        jwtToken = user["token"]
        del user["token"]

        server_session_id = await generate_server_session(jwtToken, user["id"])

        return RedirectResponse(url=f"{os.getenv('OAUTH_SUCCESS_REDIRECT_URL')}?token={server_session_id}")

    except Exception as e:

        return RedirectResponse(url=f"{os.getenv('OAUTH_SUCCESS_REDIRECT_URL')}?error={e}")

@authRouter.get("/google")
def google_auth():
    authorization_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={os.getenv('GOOGLE_CLIENT_ID')}"
        "&response_type=code"
        f"&redirect_uri={os.getenv('GOOGLE_REDIRECT_URI')}"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=authorization_url)

@authRouter.get("/google/callback", include_in_schema=False)
async def google_callback(code: str):
    try:
        user_info = await get_google_user_info(code)

        if not user_info:
            return {"success": False, "message": "Failed to get user info from Github, try again later."}
        
        user = await OAuthLoginHandler(user_info)
        
        jwtToken = user["token"]
        del user["token"]

        server_session_id = await generate_server_session(jwtToken, user["id"])
        
        return RedirectResponse(url=f"{os.getenv('OAUTH_SUCCESS_REDIRECT_URL')}?token={server_session_id}")

    except Exception as e:

        return RedirectResponse(url=f"{os.getenv('OAUTH_SUCCESS_REDIRECT_URL')}?error={e}")

@authRouter.get("/oauth/{session_id}", status_code=status.HTTP_200_OK)
async def get_current_user_session(session_id: str):
    """
    Returns the user oauth protected session details.
    """
    try:

        if not session_id:
            raise Exception("Session ID is required")
        
        session_content = Database.getOrNullStoredOauthSession(session_id)

        if not session_content:
            raise Exception("Invalid session ID")
        
        user = session_content["uid"]
        token =  session_content["token"]

        await Database.delete("oauth_session_tokens", session_id)

        response = JSONResponse(
            content={"success": True, "user": user, "token": token},
            headers={"Authorization": f"Bearer {token}"},
        )

        return response

    except Exception as e:
        return {"success": False, "message": str(e)}
