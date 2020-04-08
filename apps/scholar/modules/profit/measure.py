from easydict import EasyDict as edict
from copy import copy

from ..constants.states import NO_POSITION, SHORT_POSITION, LONG_POSITION

LENDING_PERIOD = 86400


class Accountant:
    class Describe:

        def __init__(self):
            self.data = edict(
                position=1, commission=0, lending_debt=0, profit=1, acc_profit=1, close=1,
                state=NO_POSITION
            )
            self.last_order = copy(self.data)

        def describe_profit(self, row, stop_loss=0.85, acc_stop_loss=.725, rate=9e-4, leverage=1,
                            lending_rate=1e-4):

            time = (row.date - row.date_previous).total_seconds() / LENDING_PERIOD

            if self.data.acc_profit > acc_stop_loss:
                if row.change:
                    self.last_order = copy(self.data)
                    if row.trend > 0:  # buy order
                        state = LONG_POSITION
                        if self.data.state < 0:  # close short and open long
                            lending_debt = self.data.lending_debt * (1 + lending_rate) ** time
                            commission = self.data.position * rate
                            position = self.data.position / row.close - commission - lending_debt
                            profit = (position * row.close) / (
                                    self.data.position - lending_debt * row.close)

                            lending_debt = 0
                        else:  # open long
                            lending_debt = 0
                            commission = self.data.position * rate
                            position = self.data.position / row.close - commission - lending_debt
                            profit = (position * row.close) / (
                                    self.data.position - lending_debt * row.close)
                        acc_profit = position * row.close / 1
                    elif row.trend < 0:  # sell order
                        state = SHORT_POSITION
                        if self.data.state > 0:  # close long and open short
                            # self.last_order.state = LONG_POSITION

                            # close long
                            commission = self.data.position * row.close * rate
                            lending_debt = 0
                            position = self.data.position * row.close - commission - lending_debt

                            # open short
                            lending_debt = position * leverage / row.close  # unit = other
                            commission += position * leverage * rate  # unit = mine
                            position = position * (1 + leverage) - commission  # unit = mine
                            profit = (position - lending_debt * row.close) / (
                                    self.data.position * row.close)
                        else:  # open short
                            lending_debt = self.data.position * leverage / row.close  # unit = other
                            commission = self.data.position * leverage * rate  # unit = mine
                            position = self.data.position * (
                                    1 + leverage) - commission  # unit = mine
                            profit = (position - lending_debt * row.close) / self.data.position
                        acc_profit = (position - lending_debt * row.close) / 1
                    else:
                        print(row)
                        raise Exception
                else:
                    if self.data.state > 0:  # hold long
                        state = LONG_POSITION

                        commission = 0
                        lending_debt = 0
                        position = self.data.position
                        profit = position * row.close / (
                                self.last_order.position - self.last_order.lending_debt * self.last_order.close)
                        acc_profit = position * row.close / 1
                    elif self.data.state < 0:  # hold short
                        state = SHORT_POSITION

                        last_order_position = self.last_order.position * self.last_order.close if self.last_order.state > 0 else self.last_order.position

                        commission = 0
                        lending_debt = self.data.lending_debt * (1 + lending_rate) ** time
                        position = self.data.position
                        profit = (position - lending_debt * row.close) / last_order_position
                        acc_profit = (position - lending_debt * row.close) / 1
                    else:
                        state = NO_POSITION

                        lending_debt = 0
                        commission = 0
                        position = self.data.position
                        profit = self.data.profit
                        acc_profit = position / 1
            else:
                state = self.data.state
                lending_debt = self.data.lending_debt
                commission = self.data.commission
                position = self.data.position
                profit = self.data.profit
                acc_profit = self.data.acc_profit

            if profit < stop_loss or acc_profit < acc_stop_loss:
                # uses the self.data previously computed
                # we assume next_row.open == row.close -> this is the selling/buying price
                if state > 0:  # close long
                    commission = position * row.close * rate
                    position = position * row.close - commission - lending_debt
                    # profit = position / (self.last_order.position - self.last_order.lending_debt * self.last_order.close)
                elif state < 0:  # close short
                    last_order_position = self.last_order.position * self.last_order.close if self.last_order.state > 0 else self.last_order.position

                    commission = lending_debt * row.close * rate
                    position = position - commission - lending_debt * row.close
                    # profit = position / last_order_position

                    lending_debt = 0
                if profit < stop_loss:
                    profit = stop_loss

                state = NO_POSITION
                acc_profit = position / 1

            self.data = edict(
                position=position, commission=commission, lending_debt=lending_debt, profit=profit,
                acc_profit=acc_profit, close=row.close, state=state
            )

            return self.data

    class Evaluate:

        def __init__(self, initial_position=1):
            self.initial_position = initial_position
            self.position = initial_position

        def evaluate_profit(self, row, stop_loss=0.85, rate=9e-4, leverage=1, lending_rate=1e-4):
            if row.change_start:
                ratio = row.close_end / row.close_start
                if row.state_start < 0:  # short position
                    time = (row.date_end - row.date_start).total_seconds() / LENDING_PERIOD  # per day
                    interest = (1 + lending_rate) ** time
                    profit = 1 + leverage * (1 - rate - (1 + rate) * interest * ratio)
                    # profit = 1 + leverage * (1 - rate) - leverage * interest * ratio * (1 + rate)
                elif row.state_start > 0:  # long position
                    profit = ratio * (1 - rate) ** 2
                else:
                    raise Exception
            else:
                profit = 1

            if profit < stop_loss:
                profit = stop_loss * (1 - rate)

            self.position *= profit

            return edict(
                position=self.position, profit=profit,
                acc_profit=self.position / self.initial_position
            )
