from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic_settings import BaseSettings
import models as models


class Settings(BaseSettings):
    # database configurations
    DATABASE_URL: Optional[str] = None

    CHAT_REQUEST_TIME_OUT: Optional[str] = 0
    OPENROUTER_API_URL: Optional[str] = None

    CHAT_MODEL: Optional[str] = None
    TEXT_HANDLE_MODEL: Optional[str] = None
    TEXT_HANDLE_MAX_TOKENS: Optional[str] = None

    DEFAULT_PROMPT: Optional[str] = None
    DEFAULT_ADVANCED_PROMPT: Optional[str] = None

    CHAT_LIMIT_ONE_DAY_COUNT: Optional[str] = 0
    CHAT_LIMIT_RATE_TIME_PERIOD: Optional[str] = 0
    CHAT_LIMIT_RATE_COUNT: Optional[str] = 0
    OPENROUTER_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env.dev"
        orm_mode = True


async def initiate_database():
    client = AsyncIOMotorClient(Settings().DATABASE_URL)
    await init_beanie(
        database=client.get_default_database(), document_models=models.__all__
    )
