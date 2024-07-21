from typing import List
import uuid

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
            ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.ownerId = ownerId
        self.readId = readId
        self.writeId = writeId
        self.parent = parent 
        self.subFolders = subFolders
        self.files = files

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ownerId": self.ownerId,
            "readId": self.readId,
            "writeId": self.writeId,
            "parent": self.parent,
            "subFolders": self.subFolders,
            "files": self.files
        }
