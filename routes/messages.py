from datetime import datetime
import time
from typing import Optional
from fastapi import Body, APIRouter, HTTPException
from httpx import AsyncClient
from passlib.context import CryptContext
from commons.costants import HTTP_STATUS_CODE_200_OK
from models.api import AdvancedChatReq, ChatReq, Response
from services.analysis import (
    analyze_most_active_time_period,
    analyze_most_active_topics,
)
from services.messages import (
    ai_chat,
    ai_chat_advanced,
    get_chat_history,
    get_chat_status_today_by,
)

router = APIRouter()
client = AsyncClient()

hash_helper = CryptContext(schemes=["bcrypt"])


@router.post(
    "/get_ai_chat_response",
    response_model=Response,
    summary="AI 对话",
)
async def get_ai_chat_response(req: ChatReq = Body(...)):
    """

    Description:
    - 用户输入问题，返回 AI 的回答

    Request body:
    - message 用户输入的聊天内容 **required**
    - user_name 聊天的人名字 **required**
    - middle_out_mode 超出长度时的压缩处理模式，默认:trim **optional**
        - trim 通过剪掉中间词句内容进行压缩
        - summarition 通过对中间词句内容文本摘要进行压缩
        - ignore 忽略不作处理，openrouter接口默认已通过 **transforms: ["middle-out"]** 处理
    - max_tokens 发送对话最大token **optional**

    Response body:
    - code 请求操作内部响应码
    - data 请求响应内容
        - response AI 的本次问题回答
    """
    ret = await ai_chat(client, req)
    return {
        "code": HTTP_STATUS_CODE_200_OK,
        "data": ret,
    }


@router.get(
    "/get_user_chat_history",
    response_model=Response,
    summary="查询用户聊天记录",
)
async def get_user_chat_history(user_name: str, last_n: int):
    """
    Description:
    - 根据输入参数输出用户的聊天记录

    Query Params:
    - user_name 聊天的人名字 **required**
    - last_n 输出最后 n 条聊天记录 **required**

    Response Body:

    ```
    [
        {
            "type": "user",
            "text": "hi, my name is Eric"
        },
        {
            "type": "ai",
            "text": "Hi Eric, what can I do for you!"
        }
    ]
    ```
    """
    messages = await get_chat_history(user_name, last_n)
    return {
        "code": HTTP_STATUS_CODE_200_OK,
        "data": messages,
    }


@router.get("/get_chat_status_today", response_model=Response, summary="查询用户当天聊天次数")
async def get_chat_status_today(user_name: str):
    """
    Description:
    - 返回用户当天聊天次数，对应后面做聊天控制的要求

    Query Params:
    - user_name 聊天的人名字 **required**

    Response Body:

    ```
    {
        "user_name": "xxx",
        "chat_cnt": 3
    }
    ```
    """
    ret = await get_chat_status_today_by(user_name)
    return {
        "code": HTTP_STATUS_CODE_200_OK,
        "data": ret,
    }


@router.post(
    "/get_ai_chat_response_advanced",
    response_model=Response,
    summary="AI 对话(高级, 自定义 Prompt) - 扩展",
)
async def get_ai_chat_response_advanced(req: AdvancedChatReq = Body(...)):
    """
    目前情感分析通过自定义Prompt中实现，可通过接口参数指定自定义Prompt。如：
    > 你是一个聊天机器人，你会分析用户消息中的情绪倾向(如正面、负面或中性)，当用户发送的消息中情绪倾向偏负面时，你会调整回复的语气和内容，以更好地适应用户的情绪状态

    Description:
    - 实现情感分析功能的AI对话
    - 分析用户消息的情绪倾向(如正面、负面或中性)，并用来调整 AI 回复的语气和内容，以更好地适应用户的情绪状态。

    Request body:
    - message 用户输入的聊天内容 **required**
    - user_name 聊天的人名字 **required**
    - prompt 自定义Prompt **optional**
    - middle_out_mode 超出长度时的压缩处理模式，默认:trim **optional**
        - trim 通过剪掉中间词句内容进行压缩
        - summarition 通过对中间词句内容文本摘要进行压缩
        - ignore 忽略不作处理，openrouter接口默认已通过 **transforms: ["middle-out"]** 处理
    - max_tokens 发送对话最大token **optional**

    Response body:
    - code 请求操作内部响应码
    - data 请求响应内容
        - response AI 的本次问题回答
    """
    ret = await ai_chat_advanced(client, req)
    return {
        "code": HTTP_STATUS_CODE_200_OK,
        "data": ret,
    }


@router.get(
    "/get_user_behavior",
    response_model=Response,
    summary="用户行为分析 - 扩展",
)
async def get_user_behavior(
    user_name: str,
    analysis_messages_count: Optional[int] = 100,
    active_hours_top_n: Optional[int] = 3,
    active_topics_top_n: Optional[int] = 3,
):
    """
    通过transformers, scikit-learn, pandas等分析用户聊天记录，目前实现了消息文本分析常见词汇，与活跃聊天时间段分析

    Description:
    - 返回用户聊天记录中最常讨论的主题、活跃时间段等信息
    - 基于用户与 AI 的聊天历史，分析用户的兴趣点和行为模式。
    - 通过 get_user_behavior API 提供用户行为分析的摘要报告。
    - 分析报告应包括用户最常讨论的主题、活跃时间段等信息。

    Query Params:
    - user_name 聊天的人名字 **required**
    - analysis_messages_count 分析消息的数量，默认100 **optional**
    - active_hours_top_n 返回多少个活跃时间段，默认3 **optional**
    - active_topics_top_n 返回多少个最常讨论的主题，默认3 **optional**

    Response Body:

    ```
    {
        "active_hours": [
            "1:00-2:00",
            "2:00-3:00",
            "17:00-18:00"
        ],
        "active_topics": [
            "member",
            "friend",
            "help"
        ]
    }
    ```
    """
    active_hours = await analyze_most_active_time_period(
        user_name, analysis_messages_count, active_hours_top_n
    )
    active_topics = await analyze_most_active_topics(
        user_name, analysis_messages_count, active_topics_top_n
    )
    return {
        "code": HTTP_STATUS_CODE_200_OK,
        "data": {
            "active_hours": active_hours,
            "active_topics": active_topics,
        },
    }
