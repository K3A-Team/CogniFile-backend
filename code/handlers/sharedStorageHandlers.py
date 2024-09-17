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

async def getUserSharedStorages(userId):

    sharedStorages = Database.getUserSharedStorages(userId)

    print(sharedStorages)

    return sharedStorages