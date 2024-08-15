from datetime import datetime
import uuid

class FileHash:
    """
    Represents a file hash entity in the file management system.
    """
    def __init__(
            self, 
            filename: str,
            hash: str,
            folderId: str,
            ownerId: str,
            id: str = None,
            uploaded_at: str = None
        ):
        self.id = id or str(uuid.uuid4())
        self.hash = hash
        self.ownerId = ownerId
        self.folderId = folderId
        self.filename = filename
        self.uploaded_at = uploaded_at or datetime.utcnow().isoformat()  # Default to current timestamp if not provided

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "hash": self.hash,
            "ownerId": self.ownerId,
            "folderId": self.folderId,
            "uploaded_at": self.uploaded_at,
        }
