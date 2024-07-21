from services.chatbotService import chatbot_service

async def chatbot_handler(query):
    result = chatbot_service(query)
    return result