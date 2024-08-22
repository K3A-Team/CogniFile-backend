from typing import List
import uuid
from Core.Shared.Database import db
from firebase_admin import firestore
import datetime

class Folder:
    """
    Represents a folder entity in the file management system.
    """
    def __init__(
            self, 
            name: str,
            ownerId: str,
            parent: str, 
            id: str = None, 
            readId: List[str] = [], 
            writeId: List[str] = [],
            subFolders: List[str] = [], 
            files: List[str] = [],
            interactionDate = None
            ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.ownerId = ownerId
        self.readId = readId
        self.writeId = writeId
        self.parent = parent 
        self.subFolders = subFolders
        self.interactionDate = interactionDate or datetime.datetime.now().isoformat()
        self.files = files

    @staticmethod
    def loadWithId(id):
        """
        Retrieves a folder entity from the database using its ID.

        Returns:
            Folder: The folder entity.
        """
        folder_ref = db.collection('folders').document(id)
        folder_snapshot = folder_ref.get()
        
        folderDict = folder_snapshot.to_dict()

        return Folder(
            id= folderDict['id'],
            name= folderDict['name'],
            ownerId= folderDict['ownerId'],
            readId= folderDict['readId'],
            writeId= folderDict['writeId'],
            parent= folderDict['parent'],
            subFolders= folderDict['subFolders'],
            files= folderDict['files'],
            interactionDate= folderDict['interactionDate']

        )
    
    @staticmethod
    def loadWithDict(folderDict):

        return Folder(
            id= folderDict['id'],
            name= folderDict['name'],
            ownerId= folderDict['ownerId'],
            readId= folderDict['readId'],
            writeId= folderDict['writeId'],
            parent= folderDict['parent'],
            subFolders= folderDict['subFolders'],
            files= folderDict['files'],
            interactionDate= folderDict['interactionDate']
        )


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ownerId": self.ownerId,
            "readId": self.readId,
            "writeId": self.writeId,
            "parent": self.parent,
            "subFolders": self.subFolders,
            "files": self.files,
            "interactionDate": self.interactionDate
        }

    def createSubFolder(self, name: str) -> str:
        """
        Creates a subfolder within the current folder.

        Args:
            name (str): The name of the subfolder.
            ownerId (str): The ID of the owner of the subfolder.

        Returns:
            str: The ID of the newly created subfolder.
        """
        subfolder = Folder(name=name,ownerId= self.ownerId,parent= self.id , readId= self.readId, writeId= self.writeId)
        self.subFolders.append(subfolder.id)
        self.interactionDate = datetime.datetime.now().isoformat()
        db.collection('folders').document(subfolder.id).set(subfolder.to_dict())
        return subfolder
    
    def createFile(self, fileId ) -> str:
        """
        Creates a file within the current folder.

        Args:
            fileId (str): The ID of the file to be created.

        Returns:
            str: The ID of the newly created file.
        """
        self.files.append(fileId)
        self.interactionDate = datetime.datetime.now().isoformat()
        db.collection('files').document(fileId).update({"parent": self.id , "interactionDate": self.interactionDate})
        return fileId
    
    def createFileTransactional(self, fileId, transaction) -> str:
        """
        Creates a file within the current folder using a transaction.

        Args:
            fileId (str): The ID of the file to be created.
            transaction: The Firestore transaction object.

        Returns:
            str: The ID of the newly created file.
        """
        self.files.append(fileId)
        self.interactionDate = datetime.datetime.now().isoformat()
        transaction.update(db.collection('files').document(fileId), {"parent": self.id , "interactionDate": self.interactionDate})
        return fileId
        
    

    def getSubfolders(self):
        """
        Retrieves the subfolders of the current folder.

        Returns:
            List[Folder]: A list of subfolders.
        """
        subfolder_refs = [db.collection('folders').document(subfolder_id) for subfolder_id in self.subFolders]
        
        # Fetch all subfolders in a single batch
        subfolders_snapshot = db.get_all(subfolder_refs)
        
        #Convert snapshots to Folder instances
        subfolders = [Folder.loadWithDict(snapshot.to_dict()) for snapshot in subfolders_snapshot if snapshot.exists]
        
        return subfolders
    
    def createSubFolderTransactional(self, name: str, transaction) -> str:
        """
        Creates a subfolder within the current folder using a transaction.

        Args:
            name (str): The name of the subfolder.
            transaction: The Firestore transaction object.

        Returns:
            str: The ID of the newly created subfolder.
        """
        subfolder = Folder(name=name, ownerId=self.ownerId, parent=self.id, readId=self.readId, writeId=self.writeId)
        self.subFolders.append(subfolder.id)

        subfolderDict = subfolder.to_dict()
        subfolderDict['interactionDate'] = datetime.datetime.now().isoformat()
        
        # Use the transaction to set the new subfolder document
        transaction.set(db.collection('folders').document(subfolder.id), subfolderDict)
        
        # Update the current folder's subFolders list in the transaction
        transaction.update(db.collection('folders').document(self.id), {
            'subFolders': firestore.ArrayUnion([subfolder.id]),
            'interactionDate': datetime.datetime.now().isoformat()
        })
        
        return subfolder
