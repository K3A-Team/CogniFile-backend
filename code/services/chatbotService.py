import os
import google.generativeai as genai
from pinecone import Pinecone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_pinecone import PineconeVectorStore
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage,HumanMessage
from Core.Shared.Database import Database
from Models.Entities.ChatBotSession import ChatBotSession

MODEL_TEMP = 0.0
NUM_SEARCH_RESULTS = 5
MAX_CONV_MEMORY = 5

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

index_name = "testing-index"

index = pc.Index(index_name)

model = ChatGoogleGenerativeAI(model="gemini-1.5-flash",temperature=MODEL_TEMP,google_api_key=os.getenv("GEMINI_API_KEY"))

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

async def chatbot_service(query,userID):
  """
  Handle a chatbot query for a given user.

  This function retrieves the user's chatbot session from the database,
  reconstructs the conversation history, performs the query using a conversational
  retrieval chain, updates the conversation history with the new query and response,
  and stores the updated session back in the database.

  Args:
      query (str): The user's query to the chatbot.
      userID (str): The unique identifier of the user.

  Returns:
      str: The chatbot's response to the user's query.
  """
  # Feching DataBase for history
  user = await Database.read("users", userID)
  user_chatbot_session_id = user["chatbotSessionId"]
  db_user_chatbot_session = await Database.read("chatbotSession",user_chatbot_session_id)
  user_chatbot_session = ChatBotSession(conversation=db_user_chatbot_session["conversation"],id=db_user_chatbot_session['id'])
  user_chatbot_session_dict = user_chatbot_session.to_dict()
  user_conversation = user_chatbot_session_dict['conversation']
  # Recreating history
  full_conv = []
  for qa in user_conversation:
      full_conv.append(HumanMessage(content=qa['Human']))
      full_conv.append(AIMessage(content=qa['Ai']))
  user_chating_history = InMemoryChatMessageHistory()  
  user_chating_history.add_messages(full_conv)   
  memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,chat_memory=user_chating_history)
  
  #Perform the query
  metadata_filter={"user_id": userID}
  qa_chain = ConversationalRetrievalChain.from_llm(
      llm=model,
      retriever=vectorstore.as_retriever(search_kwargs={"filter": metadata_filter}),
      memory=memory
  )
  result = qa_chain.invoke({"question": query})
  
  #Adding the new q&a in the db
  user_conversation.append({
      "Human" : query,
      'Ai' : result['answer']
  })
  ## Checking the lenght
  if  len(user_conversation) > MAX_CONV_MEMORY:
      user_conversation.pop(0)
  user_chatbot_session.conversation = user_conversation
  await user_chatbot_session.store()
  
  # Return the chatbot response 
  return result['answer']

async def clear_chat_service(userID):
  """
  Clear the chatbot session for a given user.

  This function retrieves the user's chatbot session from the database,
  clears the session, and returns a confirmation message.

  Args:
      userID (str): The unique identifier of the user.

  Returns:
      str: A message indicating that the session was cleared successfully.
  """
  user = await Database.read("users", userID)
  user_chatbot_session_id = user["chatbotSessionId"]
  db_user_chatbot_session = await Database.read("chatbotSession",user_chatbot_session_id)
  user_chatbot_session = ChatBotSession(conversation=db_user_chatbot_session["conversation"],id=db_user_chatbot_session['id'])
  await user_chatbot_session.clear()
  return 'Session Cleared successfuly'