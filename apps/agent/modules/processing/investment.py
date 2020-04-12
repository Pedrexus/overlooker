class Investment:
    # TODO: make data class

    def __init__(self, exchange, market, strategy, state, order, amount, stop_markup, limit_markup,
                 stop_loss, acc_stop_loss, public_key, secret_key):
        self.exchange = str(exchange)  # name
        self.market = str(market)
        self.strategy = str(strategy)  # name
        self.state = state
        self.order = order
        self.amount = float(amount)
        self.stop_markup = float(stop_markup)
        self.limit_markup = float(limit_markup)
        self.stop_loss = float(stop_loss)
        self.acc_stop_loss = float(acc_stop_loss)
        self.public_key = public_key
        self.secret_key = secret_key
