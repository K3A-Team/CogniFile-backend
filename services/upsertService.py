import os
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from fastapi import UploadFile
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
import io


pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

index_name = "testing-index"

index = pc.Index(index_name)

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))

#-----------------------------------------------------------------------------------------------------------------------

async def read_file(file: UploadFile):
    file_extension = os.path.splitext(file.filename)[1]
    if file_extension.lower() == '.pdf':
        return await read_pdf(file)
    elif file_extension.lower() == '.txt':
        return await read_txt(file)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

async def read_pdf(file: UploadFile):
    content = await file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    full_text = []
    for page in pdf_reader.pages:
        full_text.append(page.extract_text())
    return '\n'.join(full_text)

async def read_txt(file: UploadFile):
    content = await file.read()
    print(content)
    return content.decode('utf-8')
    
def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def upsert_to_pinecone(chunks, file_name,id_file,userID):
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        ids = [f"{file_name}_{j}" for j in range(i, i+len(batch))]
        embeds = embeddings.embed_documents(batch)
        metadata = [{"text": chunk, "file_id": id_file, "user_id": userID} for chunk in batch]
        to_upsert = zip(ids, embeds, metadata)
        _ = index.upsert(vectors=list(to_upsert))
        
async def process_and_upsert_service(file,id_file,userID):

    text = await read_file(file)
    
    print('the extracted text : ',text)
    
    chunks = split_text(text)

    print('the extracted chunks : ',file.filename)

    upsert_to_pinecone(chunks, file.filename,id_file,userID)
    
    file.file.seek(0)