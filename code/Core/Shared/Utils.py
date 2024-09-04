from Core.Shared.Database import db
from datetime import datetime
from fastapi import HTTPException
from fastapi import status
from Core.Shared.ErrorResponses import *
from fastapi import UploadFile
from fastapi import File
from Core.Shared.Storage import *

def formatUser(id):
    """
    Args:
        id (str): The ID of the user to format.
    Returns:
        dict: The user data without the password field.
    Raises:
        google.cloud.exceptions.GoogleCloudError: If there is an error retrieving the user data.
    """
    user = db.collection("users").document(id).get().to_dict()
    del user["password"]
    return user

def emailFromId(id):
    """
    Args:
        id (str): The ID of the user to retrieve the email for.
    Returns:
        str: The email of the user.
    Raises:
        google.cloud.exceptions.GoogleCloudError: If there is an error retrieving the user data.
    """
    return db.collection("users").document(id).get().to_dict()["email"]

def extractStatus(project,userID):
    """
    Args:
        project (dict): The project data.
        userID (str): The ID of the user.
    Returns:
        str: The status of the user in the project ("OWNER", "MANAGER", or "EMPLOYEE").
    """
    if project["owner"] == userID:
        return "OWNER"
    elif project["manager"] == userID:
        return "MANAGER"
    else:
        return "EMPLOYEE"

def isDateCorrect(date):
    """
    Args:
        date (str): The date string to validate.
    Returns:
        bool: True if the date is in the correct format ('%d-%m-%Y'), False otherwise.
    """
    try:
        datetime.strptime(date, '%d-%m-%Y')
        return True
    except ValueError:
        return False

async def storeInStorageHandler(file: UploadFile = File(...)):
        """
        Stores an uploaded file in Firebase Storage and returns its public URL.
        Args:
            file (UploadFile): The file to be uploaded, with a unique filename generated using the current timestamp.
        Returns:
            str: The public URL of the stored file.
        Raises:
            google.cloud.exceptions.GoogleCloudError: If there is an error uploading the file.
        """
        time = int(datetime.now().timestamp())
        fileID = str(time) + file.filename
        file.filename = fileID
        f = file.file
        url = Storage.store(f, fileID)

        file.file.seek(0)
        
        file.file.seek(0)
        return url , fileID
    

privilege_error = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail={
        "success": False,
        "message": "User not authorized to access this resource"},
)

bad_request_error = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={
        "success": False,
        "message": "Bad request"},
)
