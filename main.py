
from fastapi import FastAPI, Depends, Header
from Routers.authRouter import authRouter
from Routers.storageRouter import storageRouter
from Routers.userRouter import userRouter
from fastapi.middleware.cors import CORSMiddleware
from Middlewares.authProtectionMiddlewares import statusProtected


#Base.metadata.create_all(engine)

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



@app.get('/')
def welcome(user: str = Depends(statusProtected)):
    return user


app.include_router(authRouter, tags=["auth"], prefix="/auth")

app.include_router(storageRouter, tags=["storage"], prefix="/storage")

app.include_router(userRouter, tags=["user"], prefix="/user")



# Start the server with the following command:
# uvicorn main:app --reload