import os
from fastapi import HTTPException
from Core.Shared.Database import Database
from google.cloud.firestore_v1.base_query import FieldFilter
from pinecone import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings

# Search and model params
MODEL_TEMP = 0.0
NUM_SEARCH_RESULTS = 5

# Prompt for query type classificatiopn "NLP search" or "File name"
QUERY_CLASSIFICATION_PROMPT_TEXT = '''Given the following user input query: {query}
Classify the query as one of the following types:

1 - File Name
2 - Natural Language Search

Guidelines:

A "File Name" typically:
Contains a file extension (e.g., .txt, .pdf, .docx)
Uses underscores, hyphens, or camel case (e.g., my_document.txt, important-file.pdf, projectReport.docx)
Does not use complete sentences or question structures

A "Natural Language Search" typically:
Uses complete sentences or phrases
May include words like "find", "search", "locate", "containing", etc.
Describes the content or context of the file rather than its exact name
Often starts with phrases like "the file that has..." or "document about..."

Respond with only the number 1 or 2, corresponding to the most likely classification.
'''
QUERY_CLASSIFICATION_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(QUERY_CLASSIFICATION_PROMPT_TEXT)

# Prompt for extracting keywords from the user's query
KEYWORD_EXTRACTION_PROMPT_TEXT = [
    (
        "system",
        "You are a helpful assistant that extractes the keywords that help identifie a document on a file management and staorage system from a user's query on a  and return them in a signle string ,return only ones that are mentioned in the query don't augment them",
    ),
    ("human", "place holder")
]

# Connection with vector Database
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
CONTENT_INDEX_NAME = "testing-index"
NAMES_INDEX_NAME = "file-names-index"
content_index = pc.Index(CONTENT_INDEX_NAME)
names_index = pc.Index(NAMES_INDEX_NAME)

# Gemini
gemini_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

# OPENAI and GOOGLE-GEN-AI Embedings
gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))
openAi_embedings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"),model="text-embedding-3-large")


# Helper function to extract the unique file's ids from the vector DB results
def extract_unique_file_ids(data):
    """
    Extract unique file IDs from vector database results.

    This function iterates through the matches in the provided data, extracts the file IDs
    from the metadata, and returns a list of unique file IDs.

    Args:
        data (dict): The data containing matches from the vector database. Each match should
                     have a 'metadata' field with a 'file_id' key.

    Returns:
        list: A list of unique file IDs extracted from the matches.
    """
    file_ids = []
    for match in data['matches']:
        if 'file_id' in match['metadata']:
            if match['metadata']['file_id'] not in file_ids :
                file_ids.append(match['metadata']['file_id'])
    return list(file_ids)

def nlp_search_service(query : str,userID : str):
    """
    Perform an NLP-based search for a given query and user ID.

    This function uses an NLP model to extract relevant information from the query,
    embeds the extracted information into a vector, and queries a content index to find
    the most relevant files for the user. It returns a list of unique file IDs that match
    the search criteria.

    Args:
        query (str): The search query provided by the user.
        userID (str): The unique identifier of the user performing the search.

    Returns:
        list: A list of unique file IDs that match the search criteria.
    """
    KEYWORD_EXTRACTION_PROMPT_TEXT[1] = ("human", query)
    infos_extraction_response = gemini_model.invoke(KEYWORD_EXTRACTION_PROMPT_TEXT)
    relevant_infos = infos_extraction_response.content
    embeded_query = gemini_embeddings.embed_query(relevant_infos)
    vectors = content_index.query(
        vector=embeded_query,
        top_k=NUM_SEARCH_RESULTS,
        filter={
            "user_id": userID
        },
        include_metadata=True            
    )
    return  extract_unique_file_ids(vectors)

def name_search_service(query,userID):
    """
    Perform a name-based search for a given query and user ID.

    This function uses an embedding model to convert the query into a vector,
    and then queries a names index to find the most relevant matches for the user.
    It returns a list of unique file IDs that match the search criteria.

    Args:
        query (str): The search query provided by the user.
        userID (str): The unique identifier of the user performing the search.

    Returns:
        list: A list of unique file IDs that match the search criteria.
    """
    embeded_query = openAi_embedings.embed_query(query)
    vectors = names_index.query(
        vector=embeded_query,
        top_k=NUM_SEARCH_RESULTS,
        filter={
            "user_id": userID
        },
        include_metadata=True            
    )
    return  extract_unique_file_ids(vectors)

def search_service(query : str,userID : str):
    """
    Perform a search based on the query and user ID.

    This function classifies the query using a language model to determine the type of search to perform.
    Depending on the classification result, it either performs a name-based search or an NLP-based search.
    It returns a list of unique file IDs that match the search criteria.

    Args:
        query (str): The search query provided by the user.
        userID (str): The unique identifier of the user performing the search.

    Returns:
        list: A list of unique file IDs that match the search criteria.
    """
    llm_prompt = QUERY_CLASSIFICATION_PROMPT_TEMPLATE.format_messages(
        query = query
    )
    classification_result = gemini_model.invoke(llm_prompt)
    
    if '1' in classification_result.content:
        return name_search_service(query=query,userID=userID)
    else :
        return nlp_search_service(query=query,userID=userID)

#--------------------------------------------

def query_search_service(query: str, tags: str, userID: str):
    """
    Perform a search based on the query or tags for a given user ID.

    This function searches for files and folders accessible to the user based on the provided query or tags.
    It retrieves the user's accessible and shared files and folders, filters them based on the search criteria,
    and returns the matched files and folders.

    Args:
        query (str): The search query provided by the user.
        tags (str): A comma-separated string of tags to filter the search results.
        userID (str): The unique identifier of the user performing the search.

    Returns:
        dict: A dictionary containing the matched files and folders.

    Raises:
        HTTPException: If neither query nor tags are provided, if both query and tags are provided,
                       if the user is not found, or if any other error occurs during the search.
    """
    try:
        if not query and not tags:
            raise HTTPException(status_code=400, detail="Either query or tags must be provided")
        if query and tags:
            raise HTTPException(status_code=400, detail="Only one of query or tags should be provided")

        refs = Database.setupRefs(["files", "folders", "users"])
        files_ref = refs["files"]
        folders_ref = refs["folders"]
        users_ref = refs["users"]

        tag_list = []
        if tags:
            tag_list = [tag.strip().lower() for tag in tags.split(',') if tag.strip()]

        user_doc = users_ref.document(userID).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User not found")

        accessible_files = files_ref.where(filter=FieldFilter("ownerId", "==", userID)).stream()
        accessible_folders = folders_ref.where(filter=FieldFilter("ownerId", "==", userID)).stream()

        shared_files_r = files_ref.where(filter=FieldFilter("readId", "array_contains", userID)).stream()
        shared_files_w = [
            doc for doc in files_ref.where(filter=FieldFilter("writeId", "array_contains", userID)).stream()
            if doc.id not in {file.id for file in shared_files_r}
        ]
        
        shared_folders_r = folders_ref.where(filter=FieldFilter("readId", "array_contains", userID)).stream()
        shared_folders_w = [
            doc for doc in folders_ref.where(filter=FieldFilter("writeId", "array_contains", userID)).stream()
            if doc.id not in {folder.id for folder in shared_folders_r}
        ]

        all_files = list(accessible_files) + list(shared_files_r) + list(shared_files_w)
        all_folders = list(accessible_folders) + list(shared_folders_r) + list(shared_folders_w)

        all_user_ids = set()
        for item in all_files + all_folders:
            item_data = item.to_dict()
            all_user_ids.update(item_data.get("readId", []))
            all_user_ids.update(item_data.get("writeId", []))
            all_user_ids.add(item_data.get("ownerId", ""))

        user_names_map = Database.get_user_names_map(list(all_user_ids))

        matched_files = []
        matched_folders = []

        if query:
            matched_files = [
                item.to_dict() for item in all_files
                if Database.matches_search_term(item.to_dict(), query, user_names_map, userID)
            ]
            matched_folders = [
                item.to_dict() for item in all_folders 
                if Database.matches_search_term(item.to_dict(), query, user_names_map, userID)
            ]
        elif tags:
            matched_files = [
                item.to_dict() for item in all_files
                if any(tag.lower() in tag_list for tag in item.to_dict().get("tags", []))
            ]

        return {
            "files": matched_files,
            "folders": matched_folders
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
