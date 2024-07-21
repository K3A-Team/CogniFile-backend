from fastapi import APIRouter, Depends
from Middlewares.authProtectionMiddlewares import LoginProtected
from Core.Shared.Storage import *
from Core.Shared.Security import *
from Core.Shared.Utils import *
from Core.Shared.ErrorResponses import *
from Routers.foldersRouter import foldersRouter
from Routers.filesRouter import filesRouter

# Create a new APIRouter instance for storage-related routes
storageRouter = APIRouter()

# Nest foldersRouter and filesRouter inside storageRouter
storageRouter.include_router(foldersRouter, tags=["folders"], prefix="/folder")

# Nest filesRouter inside storageRouter with the prefix "/folders" and tag "files"
storageRouter.include_router(filesRouter, tags=["files"], prefix="/file")
