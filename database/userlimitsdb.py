import time
from typing import Union

from beanie import PydanticObjectId
from models.userlimits import UserLimits


userlimits_collection = UserLimits


async def add_userlimit(userlimit: UserLimits) -> UserLimits:
    obj = await userlimit.create()
    return obj


async def get_userlimit(user_name: str, use_date: str) -> UserLimits:
    obj = await userlimits_collection.find_one(
        {"user_name": user_name, "use_date": use_date}
    )
    if obj:
        return obj


async def deduct_userlimit(user_name: str, use_date: str) -> UserLimits:
    userlimit = await get_userlimit(user_name, use_date)
    if not userlimit:
        new_obj = UserLimits(
            user_name=user_name,
            chat_cnt=1,
            use_date=use_date,
            ctime=int(time.time() * 1000),
            mtime=int(time.time() * 1000),
        )
        userlimit = await add_userlimit(new_obj)
    else:
        update_query = {
            "$set": {
                "chat_cnt": userlimit.chat_cnt + 1,
                "mtime": int(time.time() * 1000),
            }
        }
        await userlimit.update(update_query)
    return userlimit


async def update_userlimit(id: PydanticObjectId, data: dict) -> Union[bool, UserLimits]:
    des_body = {k: v for k, v in data.items() if v is not None}
    update_query = {"$set": {field: value for field, value in des_body.items()}}
    obj = await userlimits_collection.get(id)
    if obj:
        await obj.update(update_query)
        return obj
    return False
