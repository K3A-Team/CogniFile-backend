from fastapi import APIRouter
from dotenv import load_dotenv
from pydantic import BaseModel
from handlers.searchHandler import nlp_search_handler


load_dotenv()

searchRouter = APIRouter()

class SearchRequest(BaseModel):
    query: str
    
@searchRouter.post("/natural_language")
async def performNaturalLanguageSearch(request: SearchRequest):
    try:
        result = await nlp_search_handler(request.query)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
    