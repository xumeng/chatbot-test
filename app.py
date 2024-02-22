import json
from fastapi import FastAPI, Depends

from config.config import initiate_database
from routes.messages import router as MessagesRouter
from routes.chatpdf import router as ChatPDFRouter

app = FastAPI()


@app.on_event("startup")
async def start_database():
    await initiate_database()


@app.get("/", tags=["Root"], summary="ping server")
async def ping():
    return {"message": "Hello world"}


app.include_router(MessagesRouter, tags=["聊天"])

app.include_router(ChatPDFRouter, tags=["ChatPDF"])
