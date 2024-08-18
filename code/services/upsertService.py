import os,io
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
from langchain_community.document_loaders.dataframe import DataFrameLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from docx import Document

ROWS_FOR_ONE_CHUNCK= 20

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

CONETNT_INDEX_NAME = "testing-index"
NAMES_INDEX_NAME = "file-names-index"

conetnt_index = pc.Index(CONETNT_INDEX_NAME)
names_index = pc.Index(NAMES_INDEX_NAME)

gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))
openAi_embedings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"),model="text-embedding-3-large")

#-----------------------------------------------------------------------------------------------------------------------

# Reading style sheet values as rows (CSV,XLSX)
async def read_style_sheet(file: UploadFile):
    match os.path.splitext(file.filename)[1].lower():
        case '.csv': 
            df = pd.read_csv(file.file)
        case '.xlsx': 
            df = pd.read_excel(file.file)
        case _ :
            ValueError(f"Unsupported file format for formating : {os.path.splitext(file.filename)[1].lower()}")
    loader = DataFrameLoader(data_frame=df,page_content_column=df.columns[0])
    rows = loader.load()
    return [rows,df.columns[0]]

# Spliting rows into chunks
def split_rows(rows,page_content):
    chunks = [rows[i:i + ROWS_FOR_ONE_CHUNCK] for i in range(0, len(rows), ROWS_FOR_ONE_CHUNCK)]
    chunks = [[combine_metadata_and_content(row=row,page_content=page_content) for row in chunk] for chunk in chunks]
    chunks = [str(chunk) for chunk in chunks]
    return chunks

# Reading file values as text (TXT,PDF)
async def read_text(file: UploadFile,url):
    text = ''
    match os.path.splitext(file.filename)[1].lower():
        case '.pdf':
            loader = PyPDFLoader(url)
            pages = loader.load()
            for page in pages:
                text += page.page_content + ' '
            return text
        case '.docx':
            content = await file.read()
            doc = Document(io.BytesIO(content))
            full_text = []
            for para in doc.paragraphs:
                text += ' ' + para.text
            return text
        case '.txt':
            content = await file.read()
            return content.decode('utf-8')
        case _ :
            ValueError(f"Unsupported file format for formating : {os.path.splitext(file.filename)[1].lower()}")

# Spliting text 
def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks
    
def upsert_content_to_pinecone(chunks, file_name,file_id,batch_size,userID):
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        ids = [f"{file_name}_{j}" for j in range(i, i+len(batch))]
        embeds = gemini_embeddings.embed_documents(batch)
        metadata = [{
            "text": chunk,
            "file_id": file_id,
            "user_id": userID
        } for chunk in batch]
        to_upsert = zip(ids, embeds, metadata)
        conetnt_index.upsert(vectors=list(to_upsert))
        
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

# Helper function to transform DataFrameLoader values 
def combine_metadata_and_content(row,page_content):
    combined = dict(row.metadata)
    combined[page_content] = row.page_content
    return combined

async def process_and_upsert_service(file,name,file_id,url,userID):
    # Upserting the file's name 
    upsert_name_to_pinecone(name,file_id,userID)
    
    # Upserting the file's content
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if(file_ext == '.csv' or file_ext == '.xlsx' ):
        # Upserting rows
        rows,page_content = await read_style_sheet(file)
        chunks = split_rows(rows,page_content=page_content)
        upsert_content_to_pinecone(chunks,name,file_id,50,userID)
    else:
        # Upserting text
        text = await read_text(file,url)
        chunks = split_text(text)
        upsert_content_to_pinecone(chunks,name,file_id,100,userID)
    
    # For further use
    file.file.seek(0)
