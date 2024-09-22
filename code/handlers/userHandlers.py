from Core.Shared.ErrorResponses import *
from Core.Shared.Database import Database
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.Trails import TRIALS
from services.calcSizeService import get_bytes_from_readable_size, get_readable_file_size

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

async def updateNewTrial(userID: str, trial: str):
    """
    Updates the user's trial status to the provided trial type.

    Args:
        userID (str): The ID of the user whose trial is being updated.
        trial (str): The new trial type to be assigned.

    Returns:
        dict: The updated user's data.

    Raises:
        Exception: If the trial type is invalid.
    """
    if trial not in list(TRIALS.keys()):
        return badRequestError("Invalid trial type")
    await Database.edit("users", userID, {"trial": trial})
    return await Database.read("users", userID)

async def updateUsedSpace(userID: str, file_size: int):
    """
    Updates the user's used space to the provided value.

    Args:
        userID (str): The ID of the user whose used space is being updated.
        usedSpace (str): The new used space value.

    Returns:
        dict: The updated user's data.

    Raises:
        Exception: If the used space value is invalid.
    """
    userDetail = await Database.getUser(userID, ["usedSpace"])
    user_used_space = (userDetail["usedSpace"])

    usedSpace = get_bytes_from_readable_size(user_used_space) + file_size
    await Database.edit("users", userID, {"usedSpace": get_readable_file_size(usedSpace)})
    return await Database.read("users", userID)