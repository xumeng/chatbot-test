from beanie import Document
from pydantic import BaseModel


class UserLimitModel(BaseModel):
    user_name: str
    chat_cnt: int


class UserLimits(Document):
    user_name: str
    chat_cnt: int
    use_date: str
    ctime: int
    mtime: int

    class Config:
        json_schema_extra = {
            "example": {
                "user_name": "meng",
                "chat_cnt": 20,
                "use_date": "2024-01-29",
                "ctime": 1706275357000,
                "mtime": 1706275357000,
            }
        }

    class Settings:
        name = "userlimits"
