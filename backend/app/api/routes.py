from fastapi import APIRouter, Depends, HTTPException, status
from .dependencies import get_db, get_current_user
from ..schemas.schemas import Item, ItemCreate, UserCreate, Token
from ..models.models import Item as ItemModel, User
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from ..core.config import settings
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

@router.post("/register", response_model=User)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="ユーザー名が既に存在します。")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが無効です。",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/items/", response_model=Item)
def create_item(item: ItemCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_item = ItemModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/items/{item_id}", response_model=dict)
def delete_item(item_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"detail": f"Item with id {item_id} has been deleted."}

@router.post("/create-db", response_model=dict)
def create_db(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    from ..models.models import Base
    Base.metadata.create_all(bind=db.get_bind())
    return {"message": "データベースが作成されました。"}

@router.delete("/delete-db", response_model=dict)
def delete_db(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    from ..models.models import Base
    Base.metadata.drop_all(bind=db.get_bind())
    return {"message": "データベースが削除されました。"}

@router.delete("/delete-account", response_model=dict)
def delete_account(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_user = db.query(User).filter(User.username == user["username"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません。")
    db.delete(db_user)
    db.commit()
    return {"message": "アカウントが削除されました。"}