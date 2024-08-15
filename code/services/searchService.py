import os
from Core.Shared.Database import db
from fastapi import HTTPException
from Core.Shared.Database import Database
from google.cloud.firestore_v1.base_query import FieldFilter
import google.generativeai as genai
from pinecone import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore

MODEL_TEMP = 0.7
NUM_SEARCH_RESULTS = 5

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

index_name = "testing-index"

index = pc.Index(index_name)

model = ChatGoogleGenerativeAI(model="gemini-1.5-pro",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))

prompt = [
    (
        "system",
        "You are a helpful assistant that extractes the keywords that help identifie a document on a file management and staorage system from a user's query on a  and return them in a signle string ,return only ones that are mentioned in the query don't augment them",
    ),
    ("human", "place holder")
]
def extract_unique_file_ids(data):
    file_ids = set()
    for match in data['matches']:
        if 'file_id' in match['metadata']:
            file_ids.add(match['metadata']['file_id'])
    return list(file_ids)

def nlp_search_service(query,userID):

    prompt[1] = ("human", query)
    
    infos_extraction_response = model.invoke(prompt)
        
    relevant_infos = infos_extraction_response.content
    
    embeded_query = embeddings.embed_query(relevant_infos)
    
    vectors = index.query(
                vector=embeded_query,
                top_k=NUM_SEARCH_RESULTS,
                filter={
                    "user_id": userID
                },
                include_metadata=True            
            )
    print(vectors)
    return  extract_unique_file_ids(vectors)

#--------------------------------------------

def query_search_service(query: str, tags: str, userID: str):
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
