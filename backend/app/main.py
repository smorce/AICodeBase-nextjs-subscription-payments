from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker
import os

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
# ホストマシンのパスとコンテナ内のパスは異なる。/app/app/test.db がコンテナ内のパス
CURRENT_DIR = os.getcwd()
DATABASE_PATH = os.path.join(CURRENT_DIR, "test.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

print(f"DATABASE_PATH = {DATABASE_PATH}")
print(f"DATABASE_URL = {DATABASE_URL}")

# DATABASE_URL = sqlite:///./test.db　　　←　環境変数
# aicodebasse-backend-container          | DATABASE_PATH = /app/test.db
# aicodebasse-backend-container          | DATABASE_URL = sqlite:////app/test.db


import os

print(f"Current working directory: {os.getcwd()}")
print(f"Database file path: {DATABASE_PATH}")
print(f"File exists: {os.path.exists(DATABASE_PATH)}")
if os.path.exists(DATABASE_PATH):
    print(f"File permissions: {oct(os.stat(DATABASE_PATH).st_mode)[-3:]}")
    print(f"File owner: {os.stat(DATABASE_PATH).st_uid}")



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
        # 初期データの追加
        session = SessionLocal()
        new_item = Item(name="初期アイテム")
        session.add(new_item)
        session.commit()
        session.close()
        return {"message": "DBおよびテーブルを作成しました"}
    except SQLAlchemyError as e:
        return {"message": f"DB作成に失敗しました: {str(e)}"}


# ファイル内のテーブル構造とデータは削除されますが、空のデータベースファイルとして存在し続けます。
# そのため、osを使用してファイルを直接削除する
@app.post("/delete_db")
def delete_db():
    try:
        Base.metadata.drop_all(bind=engine)
        print("デバッグ1: テーブルを削除しました")
        if os.path.exists(DATABASE_PATH):
            print(f"デバッグ2: {DATABASE_PATH} が存在します")
            os.remove(DATABASE_PATH)
            return {"message": "DBおよびテーブルを削除しました"}
        else:
            print(f"デバッグ3: {DATABASE_PATH} が存在しません")
            return {"message": "DBファイルが存在しません"}
    except SQLAlchemyError as e:
        return {"message": f"DB削除に失敗しました: {str(e)}"}
    except OSError as e:
        return {"message": f"ファイル削除に失敗しました: {str(e)}"}

@app.post("/delete_table")
def delete_table():
    try:
        Item.__table__.drop(engine)
        return {"message": "テーブルを削除しました"}
    except SQLAlchemyError as e:
        return {"message": f"テーブル削除に失敗しました: {str(e)}"}

@app.get("/read_table")
def read_table():
    try:
        session = SessionLocal()
        items = session.query(Item).all()
        session.close()
        return {"items": [{"id": item.id, "name": item.name} for item in items]}
    except SQLAlchemyError as e:
        return {"message": f"テーブルの読み取りに失敗しました: {str(e)}"}