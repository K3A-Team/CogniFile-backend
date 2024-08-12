import os
import google.generativeai as genai
from pinecone import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_pinecone import PineconeVectorStore
from langchain_core.messages.base import BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory,InMemoryChatMessageHistory
from langchain_core.messages import AIMessage,HumanMessage

MODEL_TEMP = 0.0
NUM_SEARCH_RESULTS = 5
MAX_CONV_MEMORY = 5

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

index_name = "testing-index"

index = pc.Index(index_name)

model = ChatGoogleGenerativeAI(model="gemini-1.5-pro",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001",google_api_key=os.getenv("GEMINI_API_KEY"))

vectorstore = PineconeVectorStore(index, embeddings, text_key="text")

conversation_example = {
  "conversation": [
    {
      "human": "Hello",
      "Ai": "How can I help you?"
    },
    {
      "human": "well i think Aziz's GPA was 5.0 for a certain year",
      "Ai": "Okey thats a pretty cool information"
    },
  ]
}

def chatbot_service(query,userID):
    # Recreating history
    full_conv = []
    for qa in conversation_example['conversation']:
        full_conv.append(HumanMessage(content=qa['human']))
        full_conv.append(AIMessage(content=qa['Ai']))
    user_chating_history = InMemoryChatMessageHistory()  
    user_chating_history.add_messages(full_conv)   
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,chat_memory=user_chating_history)
    print('here is the loaded memory : ',memory.buffer_as_str)
    
    #Perform the query
    metadata_filter={"user_id": userID}
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=vectorstore.as_retriever(search_kwargs={"filter": metadata_filter}),
        memory=memory
    )
    result = qa_chain.invoke({"question": query})
    print('the overall chat history : ',result['chat_history'])
    
    #Adding the new q&a in the db
    conversation_example['conversation'].append({
        "human" : query,
        'Ai' : result['answer']
    })
    if  len(conversation_example['conversation']) > MAX_CONV_MEMORY:
        conversation_example['conversation'].pop(0)
    print(conversation_example)
    return result['answer']