from services.chatbotService import chatbot_service,clear_chat_service

async def chatbot_query_handler(query,userID):
    result = await chatbot_service(query,userID)
    return result

async def chatbot_clear_session_handler(userID):
    result = await clear_chat_service(userID=userID)
    return result