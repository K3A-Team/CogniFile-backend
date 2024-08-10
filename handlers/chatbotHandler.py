from services.chatbotService import chatbot_service

async def chatbot_handler(query,userID):
    result = chatbot_service(query,userID)
    return result