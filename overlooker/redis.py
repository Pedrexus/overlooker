from django.conf import settings
from redis import Redis, ResponseError


class MyRedis(Redis):

    def get_all_hash_dicts(self, decode=False):
        objs = []
        for key in self.keys():

            try:
                data = {**self.hgetall(key), b"hash": key}
            except ResponseError:
                continue

            if decode:
                data = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}

            objs.append(data)

        return objs


def get_redis_connection():
    return MyRedis(**settings.REDIS_CONNECTION_POOL)
