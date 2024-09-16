from fastapi import FastAPI
from .api import routes
from .core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(routes.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}