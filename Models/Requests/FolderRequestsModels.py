from pydantic import BaseModel

class CreateFolderRequest(BaseModel):
    folderName: str

