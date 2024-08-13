import uuid
from Core.Shared.Database import Database

class ChatBotSession:
    """
    Represents a user in the file management system.
    """
    def __init__(self,conversation = [],id : str = None):
        self.id = id or str(uuid.uuid4())
        self.conversation = conversation 

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversation": self.conversation
        }
    
    async def store(self):
        sessionDict = self.to_dict()
        await Database.createChatbotSession(sessionId=sessionDict['id'],sessionDict=sessionDict)
        
    async def clear(self):
        sessionDict = self.to_dict()
        sessionDict['conversation'] = []
        await Database.createChatbotSession(sessionId=sessionDict['id'],sessionDict=sessionDict)
    