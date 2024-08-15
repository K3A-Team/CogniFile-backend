from services.searchService import nlp_search_service, query_search_service

async def nlp_search_handler(query,userID):
    result = nlp_search_service(query,userID)
    return result


async def query_search_handler(query, tags, userID):
    result = query_search_service(query, tags, userID)
    return result