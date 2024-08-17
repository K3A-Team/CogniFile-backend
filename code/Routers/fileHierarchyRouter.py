from fastapi import APIRouter,Depends
from dotenv import load_dotenv
from pydantic import BaseModel
from handlers.fileHierarchyHandler import file_hierarchy_handler , confirm_hierarchy_suggestions
from Middlewares.authProtectionMiddlewares import LoginProtected

load_dotenv()

fileHierarchyRouter = APIRouter()

class FolderHierarchy(BaseModel):
    folderID : str
    
@fileHierarchyRouter.post("/file_hierarchy_suggestion")
async def performFileHierarchySuggestion(request: FolderHierarchy,userID: str = Depends(LoginProtected)):
    try:
        result = await file_hierarchy_handler(request.folderID , userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
    
@fileHierarchyRouter.get("/file_hierarchy_suggestion/{transactionId}")
async def confirmFileHierarchySuggestion(transactionId: str , userID: str = Depends(LoginProtected)):
    try:
        result =  await confirm_hierarchy_suggestions(transactionId , userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
