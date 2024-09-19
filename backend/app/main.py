from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI()


# CORSの設定
origins = [
    "http://127.0.0.1:3000",
    # "http://localhost:3000",
    # "http://frontend:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # シンプル化のため全てのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データベースの設定（SQLiteを使用）。バックエンドフォルダに作成される
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# シンプルなテーブルの定義
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/create_db")
def create_db():
    try:
        Base.metadata.create_all(bind=engine)
        return {"message": "DBおよびテーブルを作成しました"}
    except SQLAlchemyError as e:
        return {"message": f"DB作成に失敗しました: {str(e)}"}

@app.post("/delete_db")
def delete_db():
    try:
        Base.metadata.drop_all(bind=engine)
        return {"message": "DBおよびテーブルを削除しました"}
    except SQLAlchemyError as e:
        return {"message": f"DB削除に失敗しました: {str(e)}"}