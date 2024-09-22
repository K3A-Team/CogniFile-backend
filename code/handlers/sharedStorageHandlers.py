from Core.Shared.Database import Database
from Core.Shared.Storage import Storage
from Models.Entities.SharedStorage import SharedStorage
from Models.Entities.Folder import Folder
from fastapi import UploadFile ,HTTPException
from fastapi import File
from Core.Shared.Utils import storeInStorageHandler

from Core.Shared.Database import db


def validate_image(file: UploadFile = File(...)) -> UploadFile:
    valid_image_mime_types = ["image/jpeg", "image/png", "image/gif" , "image/jpg"]
    if file.content_type not in valid_image_mime_types:
        raise HTTPException(status_code=400, detail="Invalid image type")
    return file

async def createSharedStorage(userId , storageName , image: UploadFile = File(...)):
    """
    Create a shared storage for a given user.

    This function creates a shared storage for a given user.

    Args:
        userId (str): The unique identifier of the user.
        storageName (str): The name of the storage.

    Returns:
        str: The shared storage's identifier.
    """
    print("Creating shared storage")
    image = validate_image(image)

    # Create root folder
    rootFolder = Folder(
        name=storageName,
        ownerId=userId,
        parent=None,
    )

    #Create the image
    await Database.createFolder(rootFolder)
    print("Before storage")
    imageUrl , fileId = await storeInStorageHandler(image)
    print("Creating shared storage")
    storage = SharedStorage(
        name=storageName,
        imagePath=imageUrl,
        rootFolderId=rootFolder.id,
        ownerId=userId,
        readId=[userId],
        writeId=[userId]
    )
    Database.createStorage(storage)


    return storage.to_dict()

async def getSharedStorage(storageId: str):
    """
    Retrieve the shared storage with the given identifier.

    This function retrieves the shared storage with the given identifier.

    Args:
        storageId (str): The unique identifier of the shared storage.

    Returns:
        dict: The shared storage's data.
    """

    storage = await Database.read("sharedStorage", storageId)

    
    if storage is None:
        raise HTTPException(status_code=404, detail="Shared storage not found")

    return storage

async def getUserSharedStoragesHandler(userId):

    sharedStorages = await Database.getUserSharedStorages(userId)

    # Only keep imagePath , id , rootFodlerPath and name
    filtered_shared_storages = [
    {
        "imagePath": storage.get("imagePath"),
        "id": storage.get("id"),
        "rootFolderId": storage.get("rootFolderId"),
        "name": storage.get("name"),
        "members" : storage['members']
    }
    for storage in sharedStorages
    ]


    return filtered_shared_storages

async def addSharedStorageHandler(storageId , userId , userEmail):
    """
    Add a user to a shared storage.

    This function adds a user to a shared storage.

    Args:
        storageId (str): The unique identifier of the shared storage.
        userId (str): The unique identifier of the user.
        userEmail (str): The email of the user to be added.

    Returns:
        None
    """

    storage = await Database.read("sharedStorage", storageId)
    if storage is None:
        raise HTTPException(status_code=404, detail="Shared storage not found")

    if userId not in storage.get("ownerId"):
        raise HTTPException(status_code=403, detail="User is not the owner of the shared storage")

    if userEmail is None or userEmail == "":
        raise HTTPException(status_code=400, detail="User email is required")
    if userEmail is not None:
        user = await Database.getUserEmail(userEmail)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        newUserId = user.get("id")

    if newUserId in storage.get("readId"):
        raise HTTPException(status_code=400, detail="User already has access to shared storage")

    storage.get("readId").append(newUserId)
    storage.get("writeId").append(newUserId)
    await Database.edit("sharedStorage", storageId, storage)
    await updateFodlersAccessRecursive(storage.get("rootFolderId"), newUserId)


    return None

async def updateFodlersAccessRecursive(rootId , userId):
    """
    Update the access of all folders in a shared storage.

    This function updates the access of all folders in a shared storage.

    Args:
        rootId (str): The unique identifier of the root folder.
        userId (str): The unique identifier of the user.

    Returns:
        None
    """

    folder = await Database.getFolder(rootId)
    folder["readId"].append(userId)
    folder["writeId"].append(userId)
    await Database.edit("folders", folder.get("id"), folder)
    for subfolder in folder["subFolders"]:
        await updateFodlersAccessRecursive(subfolder, userId)

    return None