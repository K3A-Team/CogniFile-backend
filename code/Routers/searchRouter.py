from fastapi import APIRouter,Depends, Query
from dotenv import load_dotenv
from pydantic import BaseModel
from handlers.searchHandler import nlp_search_handler, query_search_handler
from Middlewares.authProtectionMiddlewares import LoginProtected

load_dotenv()

searchRouter = APIRouter()

class SearchRequest(BaseModel):
    query: str
    
@searchRouter.get("/query_search")
async def globalQuerySearch(
    search: str = Query(None, description="The main search query"),
    tags: str = Query(None, description="Pass csv of tags to filter the search"),
    userID: str = Depends(LoginProtected)
):
    """This endpoint is used to perform a search based on the query or tags provided"""
    try:
        result = await query_search_handler(search, tags, userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}

@searchRouter.post("/natural_language")
async def performNaturalLanguageSearch(request: SearchRequest,userID: str = Depends(LoginProtected)):
    """This endpoint is used to perform a search based on the natural language query provided"""
    try:
        result = await nlp_search_handler(request.query,userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
