from pydantic import BaseModel
from typing import Optional


class AddCategorySchema(BaseModel):
    name: str
