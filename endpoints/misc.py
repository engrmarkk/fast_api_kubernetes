from fastapi import APIRouter, status, Depends, HTTPException
from schemas import AddCategorySchema, CategorySchema
from sqlalchemy.orm import Session
from func import add_new_category, get_categories
from database import get_db
from typing import List


misc_router = APIRouter(prefix="/misc", tags=["Misc"])


@misc_router.post("/category", status_code=status.HTTP_201_CREATED)
async def add_category(request_data: AddCategorySchema, db: Session = Depends(get_db)):
    name = request_data.name
    add_new_category(db, name)
    return {"message": "Category added"}


# get categories
@misc_router.get("/categories", status_code=status.HTTP_200_OK)
async def fetch_categories(db: Session = Depends(get_db)):
    categories = get_categories(db)
    response = {
        "categories": [
            CategorySchema(id=cat.id, name=cat.name.title()).dict()
            for cat in categories
        ]
    }
    return response
