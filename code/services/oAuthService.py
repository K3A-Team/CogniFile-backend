from httpx import AsyncClient
import os

async def get_github_user_info(code: str):
    """
    Gets the user's information from GitHub.

    Args:
        token (str): The user's GitHub token.

    Returns:
        dict: The user's information from GitHub.
    """
    user = None
    
    try:
        if not code:
            raise Exception("Code is required")
        
        token_url = "https://github.com/login/oauth/access_token"
        
        async with AsyncClient() as client:
            response = await client.post(token_url, data={
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "code": code,
                "redirect_uri": os.getenv("GITHUB_REDIRECT_URI")
            }, headers={"Accept": "application/json"})
            token_response = response.json()
            access_token = token_response.get("access_token")

            if not access_token:
                raise Exception("Invalid OAuth token")

            user_info_url = "https://api.github.com/user"
            email_info_url = "https://api.github.com/user/emails"
            
            user_response = await client.get(user_info_url, headers={
                "Authorization": f"Bearer {access_token}"
            })
            email_response = await client.get(email_info_url, headers={
                "Authorization": f"Bearer {access_token}"
            })

            user_info = user_response.json()
            email_info = email_response.json()

            user_info = {
                "id": user_info["id"],
                "email": user_info["email"] if user_info["email"] else email_info[0]["email"],
                "firstName": user_info["name"].split()[0],
                "lastName": user_info["name"].split()[1],
                "oauth": f"github|{user_info['login']}",
                "password": None
            }

            user = user_info
    
        return user
    
    except Exception as e:
        raise e

async def get_google_user_info(code: str):
    """
    Gets the user's information from Google.

    Args:
        token (str): The user's Google token.

    Returns:
        dict: The user's information from Google.
    """
    user = None
    
    try:
        if not code:
            raise Exception("Code is required")
        
        token_url = "https://oauth2.googleapis.com/token"
        
        async with AsyncClient() as client:
            response = await client.post(token_url, data={
                "code": code,
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
                "grant_type": "authorization_code",
            })
            token_response = response.json()
            access_token = token_response.get("access_token")

            if not access_token:
                raise Exception("Invalid OAuth token")

            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            
            user_response = await client.get(user_info_url, headers={
                "Authorization": f"Bearer {access_token}"
            })

            user_info = user_response.json()

            user_info = {
                "id": user_info["id"],
                "email": user_info["email"],
                "firstName": user_info["name"].split()[0],
                "lastName": user_info["name"].split()[1],
                "oauth": f"google|{user_info['id']}",
                "password": None
            }

            user = user_info
    
        return user
    
    except Exception as e:
        raise e
