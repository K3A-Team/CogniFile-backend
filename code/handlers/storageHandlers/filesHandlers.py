from Models.Entities.FileHash import FileHash
from google.cloud import firestore
from Core.Shared.Database import Database
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from fastapi import UploadFile
from fastapi import File
from Models.Entities.StorageFile import StorageFile
from handlers.userHandlers import updateUsedSpace
from services.hashService import generate_file_hash, is_file_duplicate
from services.calcSizeService import get_readable_file_size
from services.maliciousDetectionService import is_file_malicious
from services.upsertService import process_and_upsert_service

async def createFileHandler(userID:str, folderId: str , file: UploadFile = File(...), force: bool | None = None):
    """
    Creates a file in the specified folder and stores it in Firebase Storage.
    Args:
        userID (str): The ID of the user creating the file.
        folderId (str): The ID of the folder where the file will be stored.
        file (UploadFile): The file to be uploaded.

    Returns:
        dict: The created file's data.

    Raises:
        Exception: If the folder ID is not specified, the folder does not exist, or the user does not have write permissions.
    """
    parentFolder = None
    readId = []
    writeId = []
    tags = []

    if folderId is None:
        raise Exception("You must specify a folder to store the file in")
    
    parentFolder = await Database.getFolder(folderId)

    if parentFolder is None:
        raise Exception("File creation in non-existing folder")

    if ((userID != parentFolder["ownerId"]) and (userID not in parentFolder["writeId"])):
        raise Exception("You are not allowed to create a folder in this directory")
    
    file_content = await file.read()
    file_hash = generate_file_hash(file_content)
    await file.seek(0)
    
    name, ext = os.path.splitext(file.filename)
    
    duplicate_check = await is_file_duplicate(file_hash, folderId)
    if duplicate_check["is_duplicate"]:
        if not force:
            raise HTTPException(status_code=400, detail="File is a duplicate! Want to proceed? Use the force parameter.")
        else:
            last_duplicate = duplicate_check["last_duplicate"]
            increment = 1

            if last_duplicate:
                last_name, last_ext = os.path.splitext(last_duplicate["filename"])
                if "_duplicate" in last_name:
                    try:
                        increment = int(last_name.split("_duplicate")[-1]) + 1
                    except ValueError:
                        pass
                else:
                    name = os.path.splitext(file.filename)[0]
            else:
                raise HTTPException(status_code=400, detail="No last duplicate found")

            name = f"{name}_duplicate{increment}{ext}"
            tags.append("duplicate")
    else:
        name = f"{name}{ext}"
    if (await is_file_malicious(file_content)):
        tags.append("malicious")

    hashObj = FileHash(
        filename=name,
        hash=file_hash,
        ownerId=userID,
        folderId=folderId,
        uploaded_at=firestore.SERVER_TIMESTAMP
    )

    url = await storeInStorageHandler(file)

    await Database.store("file_hashes", hashObj.id, hashObj.to_dict())
    
    readId = parentFolder["readId"]
    writeId = parentFolder["writeId"]
    
    file_size = len(file_content)
    fileObj = StorageFile(
        name=name,
        ownerId=userID,
        folder=folderId,
        readId=readId,
        writeId=writeId,
        url=url,
        size=get_readable_file_size(file_size),
        tags=tags,
    )


    parentFolder["files"].append(fileObj.id)
    await Database.edit("folders", folderId, parentFolder)
    await updateUsedSpace(userID, file_size)

    fileDict = await Database.createFile(fileObj)
    await process_and_upsert_service(file=file,name=name,file_id=fileObj.id,url=url,userID=userID)
    
    return fileDict

async def getFileHandler(userID:str, fileID: str):
    """
    Retrieves a file's data if the user has access permissions.

    Args:
        userID (str): The ID of the user requesting the file.
        fileID (str): The ID of the file to be retrieved.

    Returns:
        dict: The requested file's data.

    Raises:
        Exception: If the user does not have read or write permissions for the file.
    """
    file = await Database.getFile(fileID=fileID)
    if ((userID != file["ownerId"]) and (userID not in file["readId"])):
        raise Exception("You are not allowed to access this directory")
    else:
        return file