import time
from Core.Shared.Database import Database, db
from Core.Shared.ErrorResponses import *
from Middlewares.authProtectionMiddlewares import *
from Core.Shared.Security import *
import uuid
from Models.Entities.User import User
from Models.Entities.ChatBotSession import ChatBotSession
from handlers.storageHandlers.foldersHandlers import createFolderHandler , createTrashFolderHandler
from Models.Entities.PasswordResetTokens import PasswordResetTokens
from services.hashService import is_token_expired, generate_reset_token
from services.SMTPService import send_reset_email
from handlers.storageHandlers.foldersHandlers import createFolderHandler


async def registerUserHandler(firstname : str, lastname : str, email : str, password : str, oauth = None, uid = None):
    """
    Registers a new user, creates a root folder for them, and returns their data with a JWT token.

    Args:
        firstname (str): The first name of the user.
        lastname (str): The last name of the user.
        email (str): The email of the user.
        password (str): The password of the user.
        oauth (str): The OAuth provider of the user //needed only for auth proccess via OAuth.
        uid (str): The unique identifier of the user //needed only for auth proccess via OAuth.

    Returns:
        dict: The registered user's data, including a JWT token.

    Raises:
        Exception: If a user with the given email already exists.
    """
    email = email.lower()

    if oauth is None:
        result = db.collection("users").where(
            "email", "==", email).get()

        if len(result) > 0:
            raise Exception("User already exists")
    
    userId = uid if oauth else str(uuid.uuid4())

    rootFolder = await createFolderHandler(userID=userId, folderName="/")

    TrashFolderId = await createTrashFolderHandler(userID=userId)

    rootFolderId = rootFolder["id"]
    
    chatbotSession = ChatBotSession() 
    
    chatbotSessionDict = chatbotSession.to_dict()
    
    await chatbotSession.store()
    
    user = User(
        id=userId,
        firstName=firstname, 
        lastName=lastname, 
        email=email,
        password= None if not password else hashPassword(password),
        rootFolderId=rootFolderId,
        chatbotSessionId=chatbotSessionDict["id"],
        trashFolderId=TrashFolderId,
        oauth=oauth
    )

    userDict = user.to_dict()

    await Database.store("users", user.id, userDict)
    
    del userDict["password"]

    jwtToken = createJwtToken({"id": userDict["id"]})

    if oauth is None:
        del userDict["id"]

    userDict["token"] = jwtToken

    return userDict

async def loginUserHandler(email, password, oauth = None):
    """
    Authenticates a user by their email and password, and returns their data with a JWT token.

    Args:
        email (str): The email of the user.
        password (str): The password of the user.
        oauth (str): The OAuth provider of the user //needed only for auth proccess via OAuth.

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

    if not user["oauth"]:
        if user["password"] != hashPassword(password):    
            raise Exception("Invalid credentials")
    else:
        if not oauth:
            if not user["password"]:
                raise Exception("User registered with OAuth, to login using email kindly reset your password")
            elif user["password"] != hashPassword(password):
                raise Exception("Invalid credentials")
        elif user["oauth"] != oauth:
            raise Exception("User registered with different OAuth provider, kindly login with the same provider")

    del user["password"]

    jwtToken = createJwtToken({"id": user["id"]})

    if not user["oauth"]:
        del user["id"]

    user["token"] = jwtToken

    return user

async def forgetPasswordHandler(email):
    """
    Sends a password reset email to the user.

    Args:
        email (str): The email of the user.

    Returns:
        dict: A success message.

    Raises:
        Exception: If the email does not exist.
    """
    
    try:
        user_data = await Database.userByEmail(email)
        if not user_data:
            return
        
        uid = user_data["id"]

        stored_tokens = Database.getOrNullStoredToken(email)
        if stored_tokens: #check if the user has already a token and if expired or not
            stored_token_data = stored_tokens[0].to_dict()

            is_invalid_token = is_token_expired(stored_token_data["expires_at"])

            if not is_invalid_token:
                raise HTTPException(status_code=400, detail="You already requested a password reset, try again later...")
        
        random_value = str(uuid.uuid4())
        token = generate_reset_token(email, random_value)
        reset_link = f"{os.getenv('RESET_BASE_URL')}/reset-password?email={email}&token={token}"

        tokengen = PasswordResetTokens(
            id=uid,
            random_value=random_value,
            email=email,
            expires_at=int(time.time()) + 5400 # 1 hours and half for expiration
        )
        tokengenDict = tokengen.to_dict()
        await Database.store("password_reset_tokens", tokengen.id, tokengenDict)
        
        await send_reset_email(email, reset_link, user_data["firstName"]+" "+user_data["lastName"])
        
        return email
    except Exception as e:
        raise e

async def resetPasswordHandler(data):
    """
    Resets a user's password and returns a success message.

    Args:
        email (str): The email of the user.
        token (str): The password reset.
        new_password (str): The new password.

    Returns:
        dict: A success message.

    Raises:
        Exception: If the email does not exist or any step forward failed.
    """
    try:
            
        email = data["email"].lower()
        request_token = data["token"]
        request_new_password = data["new_password"]

        stored_tokens = Database.getOrNullStoredToken(email)
        if not stored_tokens:
            raise HTTPException(status_code=400, detail="Invalid email or expired reset token")

        stored_token_data = stored_tokens[0].to_dict()

        stored_random_value = stored_token_data["random_value"]
        token_expiration = stored_token_data["expires_at"]

        is_invalid_token = is_token_expired(token_expiration)

        if is_invalid_token:
            raise HTTPException(status_code=400, detail="Reset token has expired")

        generated_token = generate_reset_token(email, stored_random_value)
        if request_token != generated_token:
            raise HTTPException(status_code=400, detail="Invalid reset token")

        # Update the user's password
        await Database.edit("users", stored_token_data["id"], {"password": hashPassword(request_new_password)})

        # Delete the used reset token
        await Database.delete("password_reset_tokens", stored_token_data["id"])

        return {
            "message": "Password reset successful"
        }

    except Exception as e:
        raise e

async def OAuthLoginHandler(user_info):
    """
    Authenticates a user by their OAuth provider and returns their data with a JWT token.

    Args:
        user_info (dict): The user's information from the OAuth provider.

    Returns:
        dict: The authenticated user's data, including a JWT token.

    Raises:
        Exception: If the user does not exist.
    """
    try:
        uid = str(user_info["id"]).lower()
        user = None

        result = db.collection("users").where(
            "id", "==", uid).get()
        
        if len(result) == 0:
            user = await registerUserHandler(
                user_info["firstName"],
                user_info["lastName"],
                user_info["email"],
                None,
                user_info["oauth"],
                uid
            )
        else:
            user = await loginUserHandler(user_info["email"], None, user_info["oauth"])

        return user
    except Exception as e:
        raise e
