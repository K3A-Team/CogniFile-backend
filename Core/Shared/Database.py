import firebase_admin
from firebase_admin import credentials,auth
from firebase_admin import firestore
import json
import os
from dotenv import load_dotenv
load_dotenv()

STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../../firebase.json")

cred = credentials.Certificate(CREDENTIALS_PATH)
firebase_admin.initialize_app(cred,{
        'storageBucket': STORAGE_BUCKET
    })

db = firestore.client()

class Database:

    """
    This class provides a collection of static methods for interacting with a Firestore database.

    The methods in this class are designed to perform various database operations such as:
    - Adding new documents to collections
    - Retrieving documents from collections
    - Updating existing documents
    - Deleting documents from collections

    Each method is implemented as a static method, meaning they can be called on the class itself without needing to instantiate an object of the class. This design choice makes it convenient to use these methods as utility functions for database operations throughout the application.

    The class leverages the Firestore client library to communicate with the Firestore database, ensuring that all interactions are handled efficiently and securely.

    Overall, this class serves as a centralized utility for all Firestore database interactions, promoting code reusability and maintainability.
    """

    @staticmethod
    async def store(collection , document , dict):

        doc_ref = db.collection(collection).document(document)
        return doc_ref.set(dict)


    @staticmethod
    async def read(collection , document):
        doc_ref = db.collection(collection).document(document)
        if doc_ref.get().exists:
            return doc_ref.get().to_dict()
        else:
            return None
 

    @staticmethod
    async def edit(collection , document,querydict):
        doc_ref = db.collection(collection).document(document)
        return  doc_ref.update(querydict)


    @staticmethod
    async def delete(collection , document):
        event_ref = db.collection(collection).document(document)
        return event_ref.delete()
    
    @staticmethod
    async def exists(collection,document):
        doc_ref = db.collection(collection).document(document)
        return doc_ref.get().exists

    @staticmethod
    async def userByEmail(email):
        result = db.collection("users").where("email", "==", email.lower()).get()
        if len(result) == 0:
            return None
        return result[0].to_dict()
    
    @staticmethod
    async def createFolder(folder):
        folderDict = folder.to_dict()
        await Database.store("folders", folder.id, folderDict)
        return folderDict
    
    @staticmethod
    async def getFolder(folderID):
        return await Database.read("folders", folderID)
    
    @staticmethod
    async def editFolder(folderID, folderDict):
        return await Database.edit("folders", folderID, folderDict)
    
    @staticmethod
    async def deleteFolder(folderID):
        return await Database.delete("folders", folderID)
    
    @staticmethod
    async def createFile(file):
        fileDict = file.to_dict()
        await Database.store("files", file.id, fileDict)
        return fileDict
    
    @staticmethod
    async def getFile(fileID):
        return await Database.read("files", fileID)
    
    @staticmethod
    async def editFile(fileID, fileDict):
        return await Database.edit("files", fileID, fileDict)
    
    @staticmethod
    async def deleteFile(fileID):
        return await Database.delete("files", fileID)