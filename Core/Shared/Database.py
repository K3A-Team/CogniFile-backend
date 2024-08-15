from typing import Dict, List
import firebase_admin
from firebase_admin import credentials,auth
from firebase_admin import firestore
import json
import os
from dotenv import load_dotenv
load_dotenv()

STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")

cred = credentials.Certificate({
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
})
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
    async def read(collection , document, attributes=None):
        doc_ref = db.collection(collection).document(document)
        if attributes:
            doc = doc_ref.get(field_paths=attributes)
        else:
            doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            return None
        
    @staticmethod
    async def readAll(collection):
        docs = db.collection(collection).stream()
        return [doc.to_dict() for doc in docs]

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
    
    async def getFilesByHashAndFolderId(hash: str, folderId: str):
        result = db.collection("file_hashes").where("hash", "==", hash.lower()).where("folderId", "==", folderId).order_by("uploaded_at").get()
        return [file.to_dict() for file in result]
    
    @staticmethod
    async def createFolder(folder):
        folderDict = folder.to_dict()
        await Database.store("folders", folder.id, folderDict)
        return folderDict
    
    @staticmethod
    async def getFolder(folderID, attributes=None):
        return await Database.read("folders", folderID, attributes)
    
    @staticmethod
    async def getUser(userID, attributes=None):
        return await Database.read("users", userID, attributes)
    
    @staticmethod
    async def getFilesDetails(fileIDs):
        filesDetails = []
        for fileID in fileIDs:
            fileDetail = await Database.getFile(fileID)
            filesDetails.append(fileDetail)
        return filesDetails
    
    @staticmethod
    async def getSubFoldersDetails(subFolderIDs):
        subFoldersDetails = []
        for subFolderID in subFolderIDs:
            fileDetail = await Database.getFolder(subFolderID)
            subFoldersDetails.append(fileDetail)
        return subFoldersDetails
    
    @staticmethod
    async def getRWUsersDetails(userIDs, attributes=None):
        read_ids = userIDs.get("readId", [])
        write_ids = userIDs.get("writeId", [])

        rUsersDetails = []
        wUsersDetails = []

        for userID in read_ids:
            userDetail = await Database.getUser(userID, attributes)
            rUsersDetails.append(userDetail)
        
        for userID in write_ids:
            if userID not in read_ids:
                userDetail = await Database.getUser(userID, attributes)
                wUsersDetails.append(userDetail)
            else:
                userDetail = next(user for user in rUsersDetails if user['id'] == userID)
                wUsersDetails.append(userDetail)
        
        return {
            "readId": rUsersDetails,
            "writeId": wUsersDetails
        }
    
    
    
    @staticmethod
    async def searchSubFoldersInFolder(folderID, searchTerm):
        folder = await Database.read("folders", folderID)
        all_files = await Database.getFilesDetails(folder.get("files", []))

        matching_files = [file for file in all_files if searchTerm.lower() in file["name"].lower()]
        return matching_files
    
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
    async def getFile(fileID, attributes=None):
        return await Database.read("files", fileID, attributes)
    
    @staticmethod
    async def editFile(fileID, fileDict):
        return await Database.edit("files", fileID, fileDict)
    
    @staticmethod
    async def deleteFile(fileID):
        return await Database.delete("files", fileID)
    
    @staticmethod
    def get_user_names_map(user_ids: List[str]) -> Dict[str, str]:
        """
        Given a list of user IDs, return a dictionary mapping user IDs to their full names.
        """
        user_names_map = {}
        if not user_ids:
            return user_names_map

        users_ref = db.collection('users').where('id', 'in', user_ids).stream()
        for user in users_ref:
            user_data = user.to_dict()
            user_names_map[user.id] = f"{user_data.get('firstName', '')} {user_data.get('lastName', '')}".strip()
        
        return user_names_map
    
    @staticmethod
    def matches_search_term(item, search_term: str, user_names_map: Dict[str, str], user_id: str) -> bool:
        """
        Checks if any of the attributes of the item match the search term, excluding items where the only matching criterion is ownerId
        and the user is the owner.
        """
        search_term = search_term.lower()
        
        if search_term in item.get('name', '').lower():
            return True

        owner_name = user_names_map.get(item.get('ownerId', ''), '').lower()
        if search_term in owner_name and item.get('ownerId') != user_id:
            return True
        
        for user_id in item.get('readId', []) + item.get('writeId', []):
            if search_term in user_names_map.get(user_id, '').lower():
                return True

        return False
    
    @staticmethod
    def setupRefs(cls: List[str]):
        if not cls:
            return None
        
        refs = {}
        for collection in cls:
            if collection == "files":
                refs[collection] = db.collection("files")
            elif collection == "folders":
                refs[collection] = db.collection("folders")
            elif collection == "users":
                refs[collection] = db.collection("users")
        
        return refs
