from fastapi import APIRouter, status, Depends
from Middlewares.authProtectionMiddlewares import LoginProtected
from Core.Shared.ErrorResponses import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from handlers.userHandlers import getProfileHandler, editProfileHandler

# Create a new APIRouter instance for user-related routes
userRouter = APIRouter()

@userRouter.get("/profile", status_code=status.HTTP_201_CREATED)
async def getProfile(userID: str = Depends(LoginProtected)):
    """
    Retrieves the profile of the authenticated user; the logic is handled inside the handler.
    """
    try:
        return await getProfileHandler(userID)
    except Exception as e:
        return {"success" : False, "message" : str(e)}

@userRouter.put("/profile", status_code=status.HTTP_201_CREATED)
async def editProfile(request : dict,userID: str = Depends(LoginProtected)):
    """
    Edits the profile of the authenticated user; the logic is handled inside the handler.
    """
    try:
        user = await editProfileHandler(request, userID)
        return {"success" : True, "user" : user}
    except Exception as e:
        return {"success" : False, "message" : str(e)}
