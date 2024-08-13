from fastapi import APIRouter, status, Depends
from Core.Shared.Database import Database, db
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import *
from Core.Shared.Security import *
import uuid
from Models.Entities.User import User
from Models.Entities.ChatBotSession import ChatBotSession
from handlers.storageHandlers.foldersHandlers import createFolderHandler

async def registerUserHandler(firstname : str, lastname : str, email : str, password : str):
    """
    Registers a new user, creates a root folder for them, and returns their data with a JWT token.

    Args:
        firstname (str): The first name of the user.
        lastname (str): The last name of the user.
        email (str): The email of the user.
        password (str): The password of the user.

    Returns:
        dict: The registered user's data, including a JWT token.

    Raises:
        Exception: If a user with the given email already exists.
    """
    email = email.lower()

    result = db.collection("users").where(
        "email", "==", email).get()

    if len(result) > 0:
        raise Exception("User already exists")
    
    userId = str(uuid.uuid4())

    rootFolder = await createFolderHandler(userID=userId, folderName="/")

    rootFolderId = rootFolder["id"]
    
    chatbotSession = ChatBotSession() 
    
    chatbotSessionDict = chatbotSession.to_dict()
    
    await chatbotSession.store()
    
    user = User(
        id=userId,
        firstName=firstname, 
        lastName=lastname, 
        email=email, 
        password=hashPassword(password),
        rootFolderId=rootFolderId,
        chatbotSessionId=chatbotSessionDict["id"]
        )

    userDict = user.to_dict()

    await Database.store("users", user.id, userDict)
    
    del userDict["password"]

    jwtToken = createJwtToken({"id": userDict["id"]})

    del userDict["id"]

    userDict["token"] = jwtToken

    return userDict

async def loginUserHandler(email,password):
    """
    Authenticates a user by their email and password, and returns their data with a JWT token.

    Args:
        email (str): The email of the user.
        password (str): The password of the user.

    Returns:
        dict: The authenticated user's data, including a JWT token.

    Raises:
        Exception: If the email does not exist or the credentials are invalid.
    """
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
