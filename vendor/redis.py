import time
import redis

redis_pool = redis.ConnectionPool(
    host="127.0.0.1", port=6379, password="Redis123!", db=0
)
redis_conn = redis.Redis(connection_pool=redis_pool)


def set(key, value, expire):
    v = redis_conn.set(key, value, expire)


def get(key):
    v = redis_conn.get(key)
    if v is not None:
        v = v.decode()
    return v


def hset(key, field, value):
    v = redis_conn.hset(key, field, value)


def hget(key, field):
    v = redis_conn.hget(key, field)
    # v = redis_conn.hmget(key, field)
    return v


def lpop(key):
    v = redis_conn.lpop(key).decode()
    return v


def lpush(key, value):
    v = redis_conn.lpush(key, value)


def rpop(key):
    v = redis_conn.rpop(key).decode()
    return v


def rpush(key, value):
    v = redis_conn.rpush(key, value)


def lindex(key):
    v = redis_conn.lindex(key, 0).decode()
    return v


def expire(key, seconds):
    redis_conn.expire(key, seconds)


def delete(key):
    v = redis_conn.delete(key)


def incr(key):
    redis_conn.incr(key)
    # redis_conn.expire(key, 30)


def can_pass_slide_window(key, time_period=30, limit_count=3):
    """
    :param time_period: time limit period
    :param limit_count: limit cout in the time period
    """
    now_ts = time.time() * 1000
    # use timestamp for value, make sure it is unique
    value = now_ts
    # slide window left side
    old_ts = now_ts - (time_period * 1000)
    # remove the data before the slide window
    redis_conn.zremrangebyscore(key, 0, old_ts)
    # get the data count of the window
    request_count = redis_conn.zcard(key)
    if not request_count or request_count < limit_count:
        # add new record
        redis_conn.zadd(key, {value: now_ts})
        redis_conn.expire(key, time_period + 10)
        return True
    return False
