from overlooker.redis import get_redis_connection


def get_all_hash_dicts():
    redis = get_redis_connection()