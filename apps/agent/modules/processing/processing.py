import pandas as pd

from overlooker.redis import get_redis_connection


class Processing:
    required_fields = [
        'exchange', 'market', 'strategy', 'state', 'order', 'amount',
        'stop loss', 'acc stop loss', 'public key', 'secret key', 'profit'
    ]

    def __init__(self):
        self.redis = get_redis_connection()

        # self.order_table = self.get_order_table()

    @staticmethod
    def validate(df: pd.DataFrame, required_fields: list):
        index = df[required_fields].dropna().index
        return df.loc[index]

    def get_order_table(self) -> pd.DataFrame:
        data = self.redis.get_all_hash_dicts(decode=True)
        table = pd.DataFrame(data)  # .set_index("hash")

        table = self.validate(table, self.required_fields)

        return table

    def set_visualized(self, hash):
        self.redis.hset(hash, 'visualized', True)

    def update_state_order(self, hash, state, order):
        self.redis.hset(hash, 'state', state)
        self.redis.hset(hash, 'order', order)


if __name__ == '__main__':
    p = Processing()
