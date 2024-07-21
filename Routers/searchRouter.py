from fastapi import APIRouter,Depends
from dotenv import load_dotenv
from pydantic import BaseModel
from handlers.searchHandler import nlp_search_handler
from Middlewares.authProtectionMiddlewares import LoginProtected

load_dotenv()

searchRouter = APIRouter()

class SearchRequest(BaseModel):
    query: str
    
@searchRouter.post("/natural_language")
async def performNaturalLanguageSearch(request: SearchRequest,userID: str = Depends(LoginProtected)):
    try:
        result = await nlp_search_handler(request.query,userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
