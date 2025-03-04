from typing import Annotated
from pydantic import BaseModel, Field, BeforeValidator
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class DocumentId(BaseModel):
    id: PyObjectId = Field(alias="_id", default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)