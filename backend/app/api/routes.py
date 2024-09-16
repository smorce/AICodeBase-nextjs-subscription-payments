from fastapi import APIRouter, Depends
from ..dependencies import get_db
from ..schemas.schemas import Item, ItemCreate
from ..models.models import Item as ItemModel
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/items/", response_model=Item)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = ItemModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    return db.query(ItemModel).filter(ItemModel.id == item_id).first()