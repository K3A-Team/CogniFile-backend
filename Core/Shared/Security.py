import hashlib
import datetime
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import  HTTPException ,status
from dotenv import load_dotenv
from base64 import b64decode
import os


load_dotenv()

TOKEN_LIFE_TIME = int(os.getenv("TOKEN_LIFE_TIME"))
HASHING_SECRET_KEY = os.getenv("HASHING_SECRET_KEY")
HASH_ALGORITHM = os.getenv("HASH_ALGORITHM")

def hashPassword(password: str):
    """
    Hashes a password using SHA-256 and returns the hexadecimal digest.

    Args:
        password (str): The plain text password to be hashed.

    Returns:
        str: The SHA-256 hash of the password in hexadecimal format.

    Raises:
        TypeError: If the provided password is not a string.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def createJwtToken(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT token with the given data and optional expiration time.

    Args:
        data (dict): The data to be encoded in the JWT token.
        expires_delta (Optional[timedelta]): The optional expiration time for the token.

    Returns:
        str: The encoded JWT token as a string.

    Raises:
        jwt.PyJWTError: If there is an error encoding the JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TOKEN_LIFE_TIME)  # Default expiration time
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, HASHING_SECRET_KEY, algorithm=HASH_ALGORITHM)
    return encoded_jwt

def decodeJwtToken(token: str):
    """
    Decodes a JWT token and returns its payload.

    Args:
        token (str): The JWT token to be decoded.

    Returns:
        dict: The decoded payload of the JWT token.

    Raises:
        HTTPException: If the token is invalid or cannot be decoded.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, b64decode(HASHING_SECRET_KEY), algorithms=[HASH_ALGORITHM])
        return payload
    except Exception as e:
        raise credentials_exception