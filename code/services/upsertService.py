import os,io,ast,json
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from fastapi import UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pandas as pd
from langchain_community.document_loaders.dataframe import DataFrameLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI

ROWS_FOR_ONE_CHUNCK = 20
TAGS_GENERATION_CHUNKS = 10
MODEL_TEMP = 0.0
SUPPORTED_EXTENSIONS = ['.csv','.xlsx','.docx','.pdf','.txt']

TAGS_GENERATION_PROMPT = '''You are an expert tagger and content analyzer. Your task is to generate an array of 3 relevant tags and a concise description for the following text, which has been extracted from a file.

File details:
File name: {file_name}
File extension: {file_extension}
Extracted content: {extracted_content}

Based on the file type,name and content provided, perform the following tasks:

1. Generate an array of 3 strings containing tags that accurately describe the main topics, themes, technologies, concepts, and key elements present in the text. The tags should be concise, relevant, and helpful for categorizing and searching for this content. Consider the following aspects when generating tags:
   * The file type and its typical use cases
   * Main subjects or topics discussed
   * Key concepts or ideas presented
   * Relevant industries or domains
   * General themes or categories that apply to the content

2. Create a brief description (2-3 sentences) that summarizes the main content, purpose, or key points of the file and it's content. This description should provide a quick overview of what the file is about.
Provide your response as a JSON object with the following structure: 
{{
    "tags": ["Tag1", "Tag2", "Tag3"],
    "description": "Description of the content..."
}}

Ensure that the 3 tags are diverse and cover various aspects of the content, but remain relevant and accurate. The description should be concise yet informative, capturing the essence of the file's content. '''

TAGS_GENERATION_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(TAGS_GENERATION_PROMPT)

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

CONETNT_INDEX_NAME = "testing-index"
NAMES_INDEX_NAME = "file-names-index"

conetnt_index = pc.Index(CONETNT_INDEX_NAME)
names_index = pc.Index(NAMES_INDEX_NAME)

gemini_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))
openAi_embedings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"),model="text-embedding-3-large")
gemini_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

#-----------------------------------------------------------------------------------------------------------------------

# Reading style sheet values as rows (CSV,XLSX)
async def read_style_sheet(file: UploadFile,name : str):
    """
    Read and parse a style sheet file (CSV or XLSX) and return its content as rows.

    This function reads the content of an uploaded file, which can be either in CSV or XLSX format.
    It uses pandas to parse the file and then loads the data into a DataFrameLoader to extract rows.
    The function returns the rows and the name of the first column.

    Args:
        file (UploadFile): The uploaded file to read and parse.

    Returns:
        list: A list containing the rows of the file and the name of the first column.

    Raises:
        ValueError: If the file format is not supported.
    """
    match os.path.splitext(name)[1].lower():
        case '.csv': 
            df = pd.read_csv(file.file)
        case '.xlsx': 
            df = pd.read_excel(file.file)
        case _ :
            ValueError(f"Unsupported file format for formating : {os.path.splitext(name)[1].lower()}")
    loader = DataFrameLoader(data_frame=df,page_content_column=df.columns[0])
    rows = loader.load()
    return [rows,df.columns[0]]

# Spliting rows into chunks
def split_rows(rows,page_content):
    """
    Split rows into chunks and combine metadata with content.

    This function splits the given rows into smaller chunks of a specified size.
    For each chunk, it combines the metadata and content of each row using the
    `combine_metadata_and_content` function. The chunks are then converted to strings.

    Args:
        rows (list): The list of rows to be split into chunks.
        page_content (str): The page content to be combined with each row's metadata.

    Returns:
        list: A list of stringified chunks, where each chunk is a list of combined metadata and content.
    """
    chunks = [rows[i:i + ROWS_FOR_ONE_CHUNCK] for i in range(0, len(rows), ROWS_FOR_ONE_CHUNCK)]
    chunks = [[combine_metadata_and_content(row=row,page_content=page_content) for row in chunk] for chunk in chunks]
    chunks = [str(chunk) for chunk in chunks]
    return chunks

# Reading file values as text (TXT,PDF)
async def read_text(file: UploadFile,url,name : str):
    """
    Split rows into chunks and combine metadata with content.

    This function splits the given rows into smaller chunks of a specified size.
    For each chunk, it combines the metadata and content of each row using the
    `combine_metadata_and_content` function. The chunks are then converted to strings.

    Args:
        rows (list): The list of rows to be split into chunks.
        page_content (str): The page content to be combined with each row's metadata.

    Returns:
        list: A list of stringified chunks, where each chunk is a list of combined metadata and content.
    """
    text = ''
    match os.path.splitext(name)[1].lower():
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
            ValueError(f"Unsupported file format for formating : {os.path.splitext(name)[1].lower()}")

# Spliting text 
def split_text(text):
    """
    Split the given text into chunks using a recursive character text splitter.

    This function splits the input text into smaller chunks of a specified size,
    with a specified overlap between chunks. It uses the RecursiveCharacterTextSplitter
    to perform the splitting.

    Args:
        text (str): The text to be split into chunks.

    Returns:
        list: A list of text chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks
    
def upsert_content_to_pinecone(chunks, file_name,file_id,batch_size,userID):
    """
    Upsert content chunks to Pinecone in batches.

    This function takes the text chunks, embeds them, and upserts them to the Pinecone index
    in batches. Each chunk is associated with metadata including the file name, file ID, and user ID.

    Args:
        chunks (list): The list of text chunks to be upserted.
        file_name (str): The name of the file.
        file_id (str): The unique identifier of the file.
        batch_size (int): The number of chunks to process in each batch.
        userID (str): The unique identifier of the user.

    Returns:
        None
    """
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
    """
    Upsert the file name to Pinecone.

    This function embeds the file name and upserts it to the Pinecone index
    along with metadata including the file ID and user ID.

    Args:
        file_name (str): The name of the file.
        file_id (str): The unique identifier of the file.
        userID (str): The unique identifier of the user.

    Returns:
        None
    """
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
    """
    Combine metadata and content from a DataFrame row.

    This function takes a row from a DataFrameLoader and combines its metadata
    with the page content.

    Args:
        row (DataFrameLoader): The row from the DataFrameLoader.
        page_content (str): The page content to be combined with the row's metadata.

    Returns:
        dict: A dictionary containing the combined metadata and content.
    """
    combined = dict(row.metadata)
    combined[page_content] = row.page_content
    return combined

async def generate_infos(name,content,extension):
    """
    Asynchronously generates tags for a given file content using the Gemini AI model.

    This function takes the file name, content, and extension as input, formats a prompt
    for the AI model, and then uses the model to generate relevant tags. It extracts
    the generated tags from the model's response and returns them as a list.

    Args:
    name (str): The name of the file.
    content (str): The content of the file to be analyzed.
    extension (str): The file extension (e.g., 'txt', 'py', 'java').

    Returns:
    list: A list of strings representing the generated tags.
    """
    # Building and sending the prompt
    llm_prompt = TAGS_GENERATION_PROMPT_TEMPLATE.format_messages(
        file_name=name,
        file_extension=extension,
        extracted_content=content
    )
    llm_result = await gemini_model.ainvoke(llm_prompt)
    # Extracting the tags
    json_start = llm_result.content.index('{')
    json_end = llm_result.content.rindex('}') + 1
    result_json = json.loads(llm_result.content[json_start:json_end])
    print(result_json)
    
    return result_json['tags'],result_json['description']

async def process_and_upsert_service(file,name,file_id,url,userID,saved_name):
    """
    Process and upsert the content of a file to Pinecone.

    This function processes the uploaded file based on its extension and upserts its content
    and name to the Pinecone index. It handles different file formats including CSV, XLSX, PDF,
    DOCX, and TXT.

    Args:
        file (UploadFile): The uploaded file to be processed.
        name (str): The name of the file.
        file_id (str): The unique identifier of the file.
        url (str): The URL of the file.
        userID (str): The unique identifier of the user.

    Returns:
        None
    """
    # Upserting the file's name 
    upsert_name_to_pinecone(name,file_id,userID)
    
    # Upserting the file's content
    file_ext = os.path.splitext(name)[1]
    if (file_ext not in SUPPORTED_EXTENSIONS):
        # No upserting (for the moment)
        return [] , ''
    if(file_ext == '.csv' or file_ext == '.xlsx' ):
        # Upserting rows
        rows,page_content = await read_style_sheet(file,name)
        chunks = split_rows(rows,page_content=page_content)
        upsert_content_to_pinecone(chunks,name,file_id,50,userID)
        # Generating tags and description
        extracted_content = ' '.join(chunks[:min(TAGS_GENERATION_CHUNKS, len(chunks))])
    else:
        # Upserting text
        text = await read_text(file,url,name)
        chunks = split_text(text)
        upsert_content_to_pinecone(chunks,name,file_id,100,userID)
        # Generating tags and description
        extracted_content = ' '.join(chunks[:min(TAGS_GENERATION_CHUNKS, len(chunks))])
    return await generate_infos(name=saved_name,content=extracted_content,extension=file_ext)

    
    # For further use
    file.file.seek(0)
