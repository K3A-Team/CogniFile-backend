from fastapi import APIRouter,Depends
from dotenv import load_dotenv
from pydantic import BaseModel
from handlers.chatbotHandler import chatbot_query_handler,chatbot_clear_session_handler
from Middlewares.authProtectionMiddlewares import LoginProtected

load_dotenv()

chatbotRouter = APIRouter()

class ChatBotPrompt(BaseModel):
    question : str
    
@chatbotRouter.post("/chatbot")
async def performChatQuestionAnswer(request: ChatBotPrompt,userID: str = Depends(LoginProtected)):
    """
    Handle POST requests to perform a chatbot question-answer interaction.

    """
    try:
        result = await chatbot_query_handler(request.question,userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}
    
@chatbotRouter.delete("/clear")
async def performSessionClearing(userID: str = Depends(LoginProtected)):
    """
    Handle DELETE requests to clear the chatbot session.

    """
    try:
        result = await chatbot_clear_session_handler(userID)
        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "message": str(e)}