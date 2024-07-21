from fastapi import Depends, HTTPException, Request
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
import jwt
from dotenv import load_dotenv
import os
load_dotenv()

HASH_ALGORITHM = os.getenv("HASH_ALGORITHM")
HASHING_SECRET_KEY = os.getenv("HASHING_SECRET_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
        detail={
            "success": False,
            "message": f"Could not validate credentials"},
    )

def LoginProtected(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, HASHING_SECRET_KEY, algorithms=[HASH_ALGORITHM])
        id: str = payload.get("id")
        if id == None:
            raise credentials_exception
        # Else , continue. (Don't raise any exception)
        return id
    except HTTPException as e:
        raise e
    except Exception:
        print("credentials exception")
        raise credentials_exception