import os
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
from langchain_community.document_loaders.dataframe import DataFrameLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_openai import OpenAIEmbeddings

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

CONETNT_INDEX_NAME = "testing-index"
NAMES_INDEX_NAME = "file-names-index"

conetnt_index = pc.Index(CONETNT_INDEX_NAME)
names_index = pc.Index(NAMES_INDEX_NAME)

gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))
openAi_embedings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"),model="text-embedding-3-large")

#-----------------------------------------------------------------------------------------------------------------------

async def read_file(file: UploadFile,url):
    match os.path.splitext(file.filename)[1].lower():
        case '.pdf':
            loader = PyPDFLoader(url)
            pages = loader.load()
            for page in pages:
                text += page.page_content + ' '
            return text
        case '.txt':
            return await read_txt(file)
        case '.csv': 
            df = pd.read_csv(file.file)
            loader = DataFrameLoader(data_frame=df,page_content_column=df.columns[0])
            rows = loader.load()
            for row in rows:
                text += row.metadata + ' '
            return text 
        case _ :
            ValueError(f"Unsupported file format for formating : {file_extension}")

async def read_txt(file: UploadFile):
    content = await file.read()
    return content.decode('utf-8')
    
def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def upsert_content_to_pinecone(chunks, file_name,id_file,userID):
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        ids = [f"{file_name}_{j}" for j in range(i, i+len(batch))]
        embeds = gemini_embeddings.embed_documents(batch)
        metadata = [{"text": chunk, "file_id": id_file, "user_id": userID} for chunk in batch]
        to_upsert = zip(ids, embeds, metadata)
        _ = conetnt_index.upsert(vectors=list(to_upsert))
        
def upsert_name_to_pinecone(file_name : str,file_id : str,userID : str):
    # meatadata 
    metadata = {"file_name": file_name, "file_id": file_id, "user_id": userID}
    # embedings 
    embedding = openAi_embedings.embed_query(file_name)
    # upserting
    to_upsert = [{
        'id' : file_id,
        'values' : embedding,
        'metadata' : metadata 
    }]
    _ = names_index.upsert(vectors=list(to_upsert))
        
async def process_and_upsert_service(file,name,id_file,userID,url):
    # Upserting the file's name 
    upsert_name_to_pinecone(name,id_file,userID)
    
    text = await read_file(file,url)
        
    chunks = split_text(text)

    upsert_content_to_pinecone(chunks, file.filename,id_file,userID)
    
    file.file.seek(0)
