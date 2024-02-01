import time
import traceback

from fastapi import HTTPException
from httpx import AsyncClient
from loguru import logger
from commons.costants import (
    HTTP_STATUS_CODE_401_UNAUTHORIZED,
    HTTP_STATUS_CODE_500_SERVER_ERROR,
    HTTP_STATUS_CODE_500_SERVICE_UNAVAILABLE,
)
from commons.enums import MIDDLE_OUT_MODE
from commons.utils import get_current_date_str
from config.config import Settings
from database.messagesdb import add_message, get_message_models
from database.userlimitsdb import deduct_userlimit, get_userlimit
from models.api import AdvancedChatReq, ChatReq
from models.userlimits import UserLimitModel
from vendor.redis import can_pass_slide_window, set, get, incr, expire
from transformers import (
    pipeline,
    BertTokenizer,
    T5Tokenizer,
    T5ForConditionalGeneration,
)


from models.messages import Messages


async def ai_chat(client, req: ChatReq):
    return await handle_ai_chat(
        client,
        req.user_name,
        req.message,
        req.middle_out_mode,
        req.max_tokens,
        Settings().DEFAULT_PROMPT,
    )


async def ai_chat_advanced(client, req: AdvancedChatReq):
    prompt = req.prompt
    if not prompt:
        prompt = Settings().DEFAULT_ADVANCED_PROMPT
    return await handle_ai_chat(
        client, req.user_name, req.message, req.middle_out_mode, req.max_tokens, prompt
    )


async def handle_ai_chat(
    client: AsyncClient,
    user_name: str,
    message: str,
    middle_out_mode: str,
    max_tokens: int,
    prompt: str,
):
    # check user limit by per 30second (一个用户每 30 秒最多发送 3 条信息)
    limit_rate_time_period = int(Settings().CHAT_LIMIT_RATE_TIME_PERIOD)
    limit_rate_count = int(Settings().CHAT_LIMIT_RATE_COUNT)

    userlimit_key_30s = "user:message-limit:per-30s:" + user_name
    can_pass = can_pass_slide_window(
        userlimit_key_30s, limit_rate_time_period, limit_rate_count
    )
    if not can_pass:
        raise HTTPException(
            status_code=HTTP_STATUS_CODE_401_UNAUTHORIZED,
            detail="exceed user limit per 30 second",
        )

    # check user limit by per day (一个用户一天最多发送 20 条信息)
    day_limit_count = int(Settings().CHAT_LIMIT_ONE_DAY_COUNT)
    userlimit = await get_userlimit(user_name, get_current_date_str())
    if userlimit and userlimit.chat_cnt > day_limit_count:
        raise HTTPException(
            status_code=HTTP_STATUS_CODE_401_UNAUTHORIZED,
            detail="exceed user limit per day",
        )

    # store user message
    ai_message = Messages(
        user_name=user_name,
        type="user",
        text=message,
        ctime=int(time.time() * 1000),
        mtime=int(time.time() * 1000),
    )
    await add_message(ai_message)

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + Settings().OPENROUTER_API_KEY,
    }
    # middle out user message
    logger.debug(f">>>>origin text: {message}")
    handle_message = handle_middle_out_text(message, middle_out_mode, max_tokens)
    logger.debug(f">>>>current text: {handle_message}")
    data = {
        "model": Settings().CHAT_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": handle_message},
        ],
    }
    try:
        timeout_seconds = int(Settings().CHAT_REQUEST_TIME_OUT)
        logger.debug(f">>>>request: timeout: {timeout_seconds}, data: {data}")
        response = await client.post(
            Settings().OPENROUTER_API_URL,
            headers=headers,
            json=data,
            timeout=timeout_seconds,
        )
        logger.debug(f">>>>response: {response.json()}")
        chat_resp = response.json()["choices"][0]["message"]["content"]
    except:
        traceback.print_exc()
        raise HTTPException(
            status_code=HTTP_STATUS_CODE_500_SERVICE_UNAVAILABLE,
            detail="request openrouter service error",
        )

    # store ai message
    ai_message = Messages(
        user_name=user_name,
        type="ai",
        text=chat_resp,
        ctime=int(time.time() * 1000),
        mtime=int(time.time() * 1000),
    )
    await add_message(ai_message)

    await deduct_userlimit(user_name, get_current_date_str())
    return {"response": chat_resp}


async def get_chat_history(user_name: str, last_n: int):
    return await get_message_models(user_name, last_n)


async def get_chat_status_today_by(user_name: str):
    day_limit_count = int(Settings().CHAT_LIMIT_ONE_DAY_COUNT)
    userlimit = await get_userlimit(user_name, get_current_date_str())
    if userlimit:
        return UserLimitModel(user_name=user_name, chat_cnt=userlimit.chat_cnt)
    return UserLimitModel(user_name=user_name, chat_cnt=day_limit_count)


def handle_middle_out_text(
    text: str, middle_out_mode: MIDDLE_OUT_MODE, max_tokens: int
):
    if middle_out_mode == MIDDLE_OUT_MODE.SUMMARITION:
        text = compress_text_with_summarition(
            text, max_tokens, Settings().TEXT_HANDLE_MODEL
        )
    elif middle_out_mode == MIDDLE_OUT_MODE.TRIM:
        text = compress_text(text, max_tokens, Settings().TEXT_HANDLE_MODEL)
    return text


def compress_text_with_summarition(text: str, max_length: int, model: str):
    tokenizer = T5Tokenizer.from_pretrained(model)
    tokens = tokenizer.tokenize(text)
    if len(tokens) > max_length:
        summarizer = T5ForConditionalGeneration.from_pretrained(model)

        start_len = max_length // 4
        end_len = max_length - start_len
        middle_text = tokenizer.convert_tokens_to_string(
            tokens[start_len - 10 : end_len + 10]
        )
        inputs = tokenizer.encode(
            "summarize: " + middle_text,
            return_tensors="pt",
            max_length=max_length // 2,
            truncation=True,
        )

        summary_ids = summarizer.generate(
            inputs, num_beams=4, max_length=5, early_stopping=True
        )
        summary = tokenizer.decode(summary_ids[0])

        # 保持开头和结尾的内容不变，将中间的一半内容压缩
        tokens = tokens[:start_len] + tokenizer.tokenize(summary) + tokens[-end_len:]
        return tokenizer.convert_tokens_to_string(tokens)
    return text


def compress_text_with_summarition_old(text: str, max_length: int, model: str):
    tokenizer = BertTokenizer.from_pretrained(model)
    tokens = tokenizer.tokenize(text)

    if len(tokens) > max_length:
        summarizer = pipeline("summarization")

        start_len = max_length // 4
        end_len = max_length - start_len

        middle_text = tokenizer.convert_tokens_to_string(
            tokens[start_len - 10 : end_len + 10]
        )
        summary = summarizer(
            middle_text,
            min_length=5,
            max_length=10,
            do_sample=False,
        )[0]["summary_text"]
        # 保持开头和结尾的内容不变，将中间的一半内容压缩
        tokens = tokens[:start_len] + tokenizer.tokenize(summary) + tokens[-end_len:]
        return tokenizer.convert_tokens_to_string(tokens)
    return text


def compress_text(text: str, max_length: int, model: str):
    tokenizer = T5Tokenizer.from_pretrained(model)
    tokens = tokenizer.tokenize(text)

    if len(tokens) > max_length:
        start_len = max_length // 4
        end_len = max_length - start_len
        tokens = tokens[:start_len] + tokens[-end_len:]
        return tokenizer.convert_tokens_to_string(tokens)
    return text
