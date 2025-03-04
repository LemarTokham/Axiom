from functools import lru_cache

from backend.mongo_client import MongoDB


@lru_cache
def get_mongo():
    pass