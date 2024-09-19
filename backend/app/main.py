from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from pydantic import BaseModel
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
CURRENT_DIR = os.getcwd()
DATABASE_PATH = os.path.join(CURRENT_DIR, "test.db")  # /app/test.db
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"           # sqlite:////app/test.db

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# パスワードハッシュ用のコンテキスト設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydanticモデル定義
class UserCreate(BaseModel):
    name: str
    password: str

class UserUpdate(BaseModel):
    name: str = None
    password: str = None

# モデル定義
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

# 依存性注入用のDBセッション取得関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# パスワードをハッシュ化する関数
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# パスワードの検証関数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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

# DBおよびテーブル削除エンドポイント
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
        User.__table__.drop(bind=engine)
        return {"message": "テーブルを削除しました"}
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,   
            detail=f"テーブル削除に失敗しました: {str(e)}"
        )

# テーブル読み取りエンドポイント
@app.get("/read_table")
def read_table(db: Session = Depends(get_db)):
    try:
        items = db.query(Item).all()
        users = db.query(User).all()
        return {
            "items": [{"id": item.id, "name": item.name} for item in items],
            "users": [{"id": user.id, "name": user.name} for user in users]
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,   
            detail=f"テーブルの読み取りに失敗しました: {str(e)}"
        )

# ユーザー作成エンドポイント
@app.post("/users/create")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        hashed_password = get_password_hash(user.password)
        new_user = User(name=user.name, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "ユーザーを作成しました", "user": {"id": new_user.id, "name": new_user.name}}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー作成に失敗しました: {str(e)}"
        )

# ユーザー更新エンドポイント
@app.put("/users/{user_id}")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.password is not None:
            user.password_hash = get_password_hash(user_update.password)
        db.commit()
        db.refresh(user)
        return {"message": "ユーザーを更新しました", "user": {"id": user.id, "name": user.name}}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー更新に失敗しました: {str(e)}"
        )

# ユーザー削除エンドポイント
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        db.delete(user)
        db.commit()
        return {"message": "ユーザーを削除しました"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー削除に失敗しました: {str(e)}"
        )