from fastapi import FastAPI, Depends, Header
from Routers.authRouter import authRouter
from Routers.storageRouter import storageRouter
from Routers.userRouter import userRouter
from Routers.searchRouter import searchRouter
from fastapi.middleware.cors import CORSMiddleware



# Initialize the FastAPI app
app = FastAPI()

# CORS middleware to allow requests from all origins
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the authentication router with the prefix "/auth" and tag "auth"
app.include_router(authRouter, tags=["auth"], prefix="/auth")

# Include the storage router with the prefix "/storage" and tag "storage"
app.include_router(storageRouter, tags=["storage"], prefix="/storage")

# Include the user router with the prefix "/user" and tag "user"
app.include_router(userRouter, tags=["user"], prefix="/user")

app.include_router(searchRouter,tags=["search"], prefix="/search" )


# Start the server with the following command:
# uvicorn main:app --reload