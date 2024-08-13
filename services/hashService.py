import hashlib
import math
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

def get_readable_file_size(size_in_bytes: int) -> str:
    if size_in_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_in_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_in_bytes / p, 2)
    return f"{s} {size_name[i]}"