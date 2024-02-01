from typing import Optional, Any

from pydantic import BaseModel

from commons.costants import HTTP_STATUS_CODE_200_OK
from commons.enums import MIDDLE_OUT_MODE
from config.config import Settings


class ChatReq(BaseModel):
    message: str
    user_name: str
    middle_out_mode: Optional[str] = MIDDLE_OUT_MODE.TRIM
    max_tokens: Optional[int] = int(Settings().TEXT_HANDLE_MAX_TOKENS)


class AdvancedChatReq(ChatReq):
    prompt: Optional[str] = None


class Response(BaseModel):
    code: int
    data: Optional[Any]

    class Config:
        schema_extra = {
            "example": {
                "code": HTTP_STATUS_CODE_200_OK,
                "data": "Sample data",
            }
        }
