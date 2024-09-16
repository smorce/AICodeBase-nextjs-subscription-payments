from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes
from .core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# CORSの設定
origins = [
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}