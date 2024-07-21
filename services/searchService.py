import os
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

vectorstore = PineconeVectorStore(index, embeddings, text_key="text")

retriever = vectorstore.as_retriever(search_kwargs={"k": NUM_SEARCH_RESULTS})


prompt = [
    (
        "system",
        "You are a helpful assistant that extractes the keywords that help identifie a document on a file management and staorage system from a user's query on a  and return them in a signle string ,return only ones that are mentioned in the query don't augment them",
    ),
    ("human", "place holder")
]


def nlp_search_service(query):

    prompt[1] = ("human", query)
    
    infos_extraction_response = model.invoke(prompt)
    
    relevant_infos = infos_extraction_response.content
    
    vectors = retriever.invoke(query)
    
    return vectors