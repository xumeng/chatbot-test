from beanie import Document
from pydantic import BaseModel


class MessagesModel(BaseModel):
    type: str
    text: str


class Messages(Document):
    user_name: str
    type: str
    text: str
    ctime: int
    mtime: int

    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "meng",
                "type": "user",
                "text": "Hi, my name is Meng",
                "ctime": 1706275357000,
                "mtime": 1706275357000,
            }
        }

    class Settings:
        name = "messages"
