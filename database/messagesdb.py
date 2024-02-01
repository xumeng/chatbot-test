from typing import List

from models.messages import Messages, MessagesModel


message_collection = Messages


async def add_message(new_message: Messages) -> Messages:
    message = await new_message.create()
    return message


async def retrieve_messages(user_name: str, last_n: int) -> List[Messages]:
    messages = (
        await message_collection.find({"user_name": user_name})
        .sort([("ctime", -1)])
        .limit(last_n)
        .to_list()
    )
    return messages


async def get_message_models(user_name: str, last_n: int) -> List[MessagesModel]:
    messages = await retrieve_messages(user_name, last_n)

    rets = [
        MessagesModel(type=item.type, text=item.text) for item in reversed(messages)
    ]
    return rets
