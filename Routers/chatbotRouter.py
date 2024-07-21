from fastapi import APIRouter,Depends
from dotenv import load_dotenv
from pydantic import BaseModel
from handlers.chatbotHandler import chatbot_handler
from Middlewares.authProtectionMiddlewares import LoginProtected

load_dotenv()

chatRouter = APIRouter()

class ChatRequest(BaseModel):
    query: str
    
@chatRouter.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await chatbot_handler(request.query)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}