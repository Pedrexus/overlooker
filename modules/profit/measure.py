from collections import UserDict
from typing import List, Tuple, Any

from pandas import DataFrame, Series

from modules.constants.orders import OPEN_LONG_POSITION, HOLD_POSITION, \
    OPEN_SHORT_POSITION, CLOSE_LONG_POSITION, \
    CLOSE_SHORT_POSITION, Order
from modules.constants.states import State, SHORT_POSITION, LONG_POSITION, NO_POSITION
from modules.strategy import Context
from modules.utils.decorators import argsdispatch


class Ledger:

    def __init__(self, cash: int = 1):
        self.orders = DataFrame(
            dict(position=[cash], commission=[0], lending_debt=[0],
                 profit=[1], is_order=[False], close=[1], state=[NO_POSITION])
        )

    def save(self, position, commission, lending_debt, profit, close, is_order, state):
        data = dict(position=position, commission=commission, lending_debt=lending_debt,
                    profit=profit, close=close, is_order=is_order, state=state)
        self.orders = self.orders.append(data, ignore_index=True)

    @property
    def last_order(self) -> Series:
        df = self.orders[self.orders.is_order]
        if len(df):
            return df.iloc[-1]
        return self.orders.iloc[0]

    @property
    def result(self):
        return self.orders.drop("close", axis=1)


OrderType = Tuple[float, float, float, float, float, bool]


class Measure:

    def __init__(self, stop_loss: float = 0.85, buy_rate=9e-4, sell_rate=9e-4, leverage=1,
                 lending_rate=2e-2, candlestick_period=300):
        self.stop_loss = stop_loss
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate
        self.leverage = leverage
        self.lending_rate = lending_rate
        self.time = candlestick_period

        self.ledger = Ledger()

    def record(self, orders: Tuple[Order], context: Context, close: float) -> Tuple[Order]:
        state = context.state
        _ = self.ledger.last_order

        position, commission, lending_debt, profit, close, is_order = self.compute_order(
            orders, state, _.position, _.commission, _.lending_debt, _.profit, close)

        # print(_.position, _.commission, _.lending_debt, _.profit)

        if profit < self.stop_loss:
            orders = (CLOSE_SHORT_POSITION,) if state is SHORT_POSITION else (CLOSE_LONG_POSITION,)

        context.update(orders)

        self.ledger.save(
            position, commission, lending_debt, profit, close, is_order, context.state)

        return orders

    @argsdispatch
    def compute_order(self, orders: Tuple[Order], state: State = NO_POSITION, position: float = 1,
                      commission: float = 0, lending_debt: float = 0, profit: float = 1,
                      close: float = 1) -> OrderType:
        raise NotImplementedError(
            f"orders {orders} is not possible. "
            f"Check strategy method"
        )

    @compute_order.register(orders=(HOLD_POSITION,))
    def hold_position(self, state, position, commission, lending_debt, profit, close):
        is_order = False

        commission = 0
        if state is LONG_POSITION:
            lending_debt = 0
            profit = position * close / (
                    position - self.ledger.last_order.lending_debt * self.ledger.last_order.close)
        elif state is SHORT_POSITION:
            lending_debt *= (1 + self.lending_rate) ** self.time
            profit = (position - lending_debt * close) / self.ledger.last_order.position
        else:
            lending_debt = 0
            profit = 1

        return position, commission, lending_debt, profit, close, is_order

    @compute_order.register(orders=(OPEN_LONG_POSITION,))
    def open_long_position(self, state, position, commission, lending_debt, profit, close):
        is_order = True

        lending_debt = 0
        commission += position * self.buy_rate  # unit = mine
        _position = position / close - commission - lending_debt  # unit = other

        profit *= (_position * close) / (position - lending_debt * close)

        return _position, commission, lending_debt, profit, close, is_order

    @compute_order.register(orders=(OPEN_SHORT_POSITION,))
    def open_short_position(self, state, position, commission, lending_debt, profit,
                            close):
        is_order = True

        leverage = position * self.leverage  # leveraged amount

        lending_debt = leverage / close  # unit = other
        commission += leverage * self.sell_rate  # unit = mine
        _position = position + leverage - commission  # unit = mine

        profit *= (_position - lending_debt * close) / position

        return _position, commission, lending_debt, profit, close, is_order

    @compute_order.register(orders=(CLOSE_LONG_POSITION,))
    def close_long_position(self, state, position, commission, lending_debt, profit,
                            close):
        is_order = True

        revenue = position * close  # gross revenue for closing position

        lending_debt = 0
        commission += revenue * self.sell_rate  # unit = mine
        _position = revenue - commission - lending_debt  # unit = mine

        profit *= (_position - lending_debt * close) / position

        return _position, commission, lending_debt, profit, close, is_order

    @compute_order.register(orders=(CLOSE_SHORT_POSITION,))
    def close_short_position(self, state, position, commission, lending_debt, profit,
                             close):
        is_order = True

        lending_debt *= (1 + self.lending_rate) ** self.time  # unit = other
        final_debt = lending_debt * close  # unit = mine

        commission += final_debt * self.buy_rate  # unit = mine
        _position = position - commission - final_debt  # unit = other

        profit *= (_position - lending_debt * close) / position

        return _position, commission, lending_debt, profit, close, is_order

    @compute_order.register(orders=(CLOSE_LONG_POSITION, OPEN_LONG_POSITION))
    def close_long_and_open_short_position(self, state, position, commission, lending_debt,
                                           profit, close):
        position, commission, lending_debt, profit, *_ = self.close_long_position(
            (CLOSE_LONG_POSITION,), position, commission, lending_debt, profit, close)
        position, commission, lending_debt, profit, close, is_order = self.open_short_position(
            (OPEN_SHORT_POSITION,), position, commission, lending_debt, profit, close)

        return position, commission, lending_debt, profit, close, is_order

    @compute_order.register(orders=(CLOSE_SHORT_POSITION, OPEN_LONG_POSITION))
    def close_short_and_open_long_position(self, state, position, commission, lending_debt,
                                           profit, close):
        position, commission, lending_debt, profit, *_ = self.close_short_position(
            (), position, commission, lending_debt, profit, close)
        position, commission, lending_debt, profit, close, is_order = self.open_long_position(
            (), position, commission, lending_debt, profit, close)

        return position, commission, lending_debt, profit, close, is_order
