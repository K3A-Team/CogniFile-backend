from Routers.storageRouter import storageRouter
from Core.Shared.ErrorResponses import *
from Core.Shared.Database import Database , db
from Core.Shared.Security import *
from Core.Shared.Utils import *

async def getProfileHandler(userID: str):
    """
    Retrieves a user's profile data by their user ID.

    Args:
        userID (str): The ID of the user whose profile is being retrieved.

    Returns:
        dict: A dictionary containing the success status and the user's data (excluding the password).

    Raises:
        Exception: If the user is not found.
    """
    user = await Database.read("users", userID)
    if user is None:
        return badRequestError("User not found")
    del user["password"]
    return {"success" : True, "user" : user}

async def editProfileHandler(data : dict,userID: str):
    """
    Edits a user's profile data based on the provided data dictionary.

    Args:
        data (dict): A dictionary containing the profile fields to update (firstName, lastName, email, password).
        userID (str): The ID of the user whose profile is being edited.

    Returns:
        dict: The updated user's data.

    Raises:
        Exception: If no data is provided to update.
    """
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