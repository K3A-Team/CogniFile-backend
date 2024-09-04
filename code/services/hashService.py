import hashlib
from fastapi import HTTPException
from Core.Shared.Database import Database , db

def generate_file_hash(file_content: bytes) -> str:
    """
    Generate a SHA-256 hash for the given file content.

    This function takes the content of a file as bytes and returns its SHA-256 hash
    as a hexadecimal string.

    Args:
        file_content (bytes): The content of the file to hash.

    Returns:
        str: The SHA-256 hash of the file content.
    """
    file_hash = hashlib.sha256(file_content).hexdigest()
    return file_hash

async def is_file_duplicate(file_hash: str, folderId: str) -> dict:
    """
    Check if a file with the given hash already exists in the specified folder.

    This function queries the database to find files with the same hash in the specified folder.
    It returns a dictionary indicating whether the file is a duplicate and the details of the last duplicate found.
    If there are more than 10 duplicates, it raises an HTTP exception to prevent further uploads.

    Args:
        file_hash (str): The SHA-256 hash of the file to check.
        folderId (str): The unique identifier of the folder to check in.

    Returns:
        dict: A dictionary with keys "is_duplicate" (bool) and "last_duplicate" (dict or None).

    Raises:
        HTTPException: If there are more than 10 duplicate files in the folder.
    """
    files = await Database.getFilesByHashAndFolderId(file_hash, folderId)

    if len(files) == 0:
        return {"is_duplicate": False, "last_duplicate": None}
    
    # If there are more than 10 duplicates, prevent further uploads
    if len(files) >= 10:
        raise HTTPException(status_code=400, detail="Cannot upload more than 10 duplicate files.")
    
    last_duplicate = files[-1]
    
    return {"is_duplicate": True, "last_duplicate": last_duplicate}
