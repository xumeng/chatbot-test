from fastapi import Body, APIRouter, HTTPException, FastAPI, UploadFile, File, Depends
from commons.costants import HTTP_STATUS_CODE_200_OK
from models.api import FileChatReq, Response
from services.chatpdf import feed_data, pdf_chat

import os

router = APIRouter()


SAVE_DIR = "./tmpdata/"
MAX_FILE_SIZE_MB = 50


async def check_file(file: UploadFile = File(...)):
    """
    check upload files
    """
    # check file type, just support pdf now
    allowed_extensions = ["pdf"]
    file_extension = file.filename.split(".")[-1]
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail="Only pdf and txt files are allowed"
        )

    # check file size
    file_size_mb = os.path.getsize(file.filename) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds the maximum allowed size of {MAX_FILE_SIZE_MB} MB",
        )
    return file


@router.post(
    "/upload_files",
    response_model=Response,
    summary="Upload file",
)
async def create_upload_file(file: UploadFile = Depends(check_file)):
    """
    上传文件，并解析开启AI对话

    Description:
    ...

    Request body:
    - file 上传的文件 **required**

    Response Body:

    ```
    {
        "sourceInfo": {
            "displayName": "xxx.pdf",
            "numBytes": 1024,
        },
        "summary": "this is a summary"
    }
    ```
    """
    # handle save file
    file_path = os.path.join(SAVE_DIR, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    # load data to llm
    summary = await feed_data(file_path)

    # show file metadata
    file_name = file.filename
    file_size_mb = os.path.getsize(file.filename) / (1024 * 1024)
    return {
        "sourceInfo": {"displayName": file_name, "numBytes": file_size_mb},
        "summary": summary,
    }


@router.post(
    "/file_chat",
    response_model=Response,
    summary="Chat with file",
)
async def file_chat(req: FileChatReq = Body(...)):
    """
    与之前上传的文件进行对话

    Description:
    ...

    Request body:
    - message 用户输入的聊天内容 **required**

    Response body:
    - code 请求操作内部响应码
    - data 请求响应内容
        - response AI的本次问题回答
    """
    ret = await pdf_chat(req)
    return {
        "code": HTTP_STATUS_CODE_200_OK,
        "data": ret,
    }
