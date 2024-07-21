from services.searchService import nlp_search_service

async def nlp_search_handler(query):
    result = nlp_search_service(query)
    return result