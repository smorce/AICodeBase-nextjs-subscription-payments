from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
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
DATABASE_PATH = os.path.join(CURRENT_DIR, "test.db")  # /app/test.db
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"           # sqlite:////app/test.db

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# モデル定義
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# 依存性注入用のDBセッション取得関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ルートエンドポイント
@app.get("/")
def read_root():
    return {"message": "Hello World"}

# DBおよびテーブル作成エンドポイント
@app.post("/create_db")
def create_db(db: Session = Depends(get_db)):
    try:
        Base.metadata.create_all(bind=engine)
        # 初期データの追加
        new_item = Item(name="初期アイテム")
        db.add(new_item)
        db.commit()
        return {"message": "DBおよびテーブルを作成しました"}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB作成に失敗しました: {str(e)}"
        )

# ファイル内のテーブル構造とデータは削除されますが、空のデータベースファイルとして存在し続けます。
# そのため、osを使用してファイルを直接削除する
@app.post("/delete_db")
def delete_db():
    try:
        # テーブルを削除
        Base.metadata.drop_all(bind=engine)

        # エンジンをディスポーズして全接続を閉じる
        engine.dispose()

        # データベースファイルを削除
        if os.path.exists(DATABASE_PATH):
            os.remove(DATABASE_PATH)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{DATABASE_PATH} が存在しません"
            )

        return {"message": "DBおよびテーブルを削除しました"}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB削除に失敗しました: {str(e)}"
        )
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ファイル削除に失敗しました: {str(e)}"
        )

# テーブル削除エンドポイント
@app.post("/delete_table")
def delete_table(db: Session = Depends(get_db)):
    try:
        Item.__table__.drop(bind=engine)
        return {"message": "テーブルを削除しました"}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,   # コンソールには 500 Internal Server Error が表示される
            detail=f"テーブル削除に失敗しました: {str(e)}"
        )

# テーブル読み取りエンドポイント
@app.get("/read_table")
def read_table(db: Session = Depends(get_db)):
    try:
        items = db.query(Item).all()
        return {"items": [{"id": item.id, "name": item.name} for item in items]}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,   # コンソールには 500 Internal Server Error が表示される
            detail=f"テーブルの読み取りに失敗しました: {str(e)}"
        )