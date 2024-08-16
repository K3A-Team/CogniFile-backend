import hashlib
import re
from fastapi import HTTPException
from Core.Shared.Database import Database

def generate_file_hash(file_content: bytes) -> str:
    file_hash = hashlib.sha256(file_content).hexdigest()
    return file_hash

async def is_file_duplicate(file_hash: str, folderId: str) -> dict:
    files = await Database.getFilesByHashAndFolderId(file_hash, folderId)

    if len(files) == 0:
        return {"is_duplicate": False, "last_duplicate": None}
    
    # If there are more than 10 duplicates, prevent further uploads
    if len(files) >= 10:
        raise HTTPException(status_code=400, detail="Cannot upload more than 10 duplicate files.")
    
    last_duplicate = files[-1]
    
    return {"is_duplicate": True, "last_duplicate": last_duplicate}
