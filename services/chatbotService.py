import os
import google.generativeai as genai
from pinecone import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_pinecone import PineconeVectorStore

MODEL_TEMP = 0.0
NUM_SEARCH_RESULTS = 5

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

index_name = "testing-index"

index = pc.Index(index_name)

model = ChatGoogleGenerativeAI(model="gemini-1.5-pro",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))

vectorstore = PineconeVectorStore(index, embeddings, text_key="text")

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


def chatbot_service(query,userID):
    metadata_filter={"user_id": userID}
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=vectorstore.as_retriever(search_kwargs={"filter": metadata_filter}),
        memory=memory
    )
    print(memory.load_memory_variables({}))
    result = qa_chain({"question": query})
    print(memory.load_memory_variables({}))
    return result['answer']