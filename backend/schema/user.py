from beanie import Document
from pydantic import BaseModel, EmailStr

from backend.schema.optional_fields import partial_model
from backend.schema.document_id import PyObjectId, DocumentId


class UserBase(BaseModel):
    username: str
    email: EmailStr
    password_hash: str
    is_admin: bool
    course: list[PyObjectId]


class UserCreate(UserBase):
    pass


@partial_model
class UserUpdate(UserBase):
    pass


class User(UserBase, DocumentId):

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


class UserDocument(User, Document):
    class Settings:
        name = "users"