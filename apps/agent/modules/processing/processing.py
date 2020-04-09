import pandas as pd

from overlooker.redis import get_redis_connection


class Processing:

    required_fields = [
        'strategy', 'profit', 'state', 'order', 'amount',
        # 'market', 'stop loss', 'acc stop loss', 'user', 'exchange'
    ]

    def __init__(self):
        self.redis = get_redis_connection()

        self.order_table = self.get_order_table()

    @staticmethod
    def validate(df: pd.DataFrame, required_fields: list):
        index = df[required_fields].dropna().index
        return df.loc[index]

    @staticmethod
    def get_order_connections(row):
        from apps.scholar.models import ExchangeConnection
        conn = ExchangeConnection.objects.get(user_id=row.user, exchange_id=row.exchange)
        return conn.public_key, conn.secret_key

    def get_order_table(self):
        data = self.redis.get_all_hash_dicts(decode=True)
        table = pd.DataFrame(data).set_index("hash")

        table = self.validate(table, self.required_fields)
        # public_key, secret_key = table.apply(self.get_order_connections, axis=1)

        # table["public_key"], table["secret_key"] = public_key, secret_key

        return table


if __name__ == '__main__':
    p = Processing()
