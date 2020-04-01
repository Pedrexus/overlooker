from modules.constants.orders import OPEN_LONG_POSITION, OPEN_SHORT_POSITION, CLOSE_SHORT_POSITION, \
    CLOSE_LONG_POSITION
from modules.constants.states import NO_POSITION, LONG_POSITION, SHORT_POSITION


class Context:
    def __init__(self):
        self.i = 0
        self.state = NO_POSITION

    def reset(self):
        self.i = 0
        self.state = NO_POSITION

    def update(self, orders):
        self.i += 1

        if OPEN_LONG_POSITION in orders:
            self.state = LONG_POSITION
        elif OPEN_SHORT_POSITION in orders:
            self.state = SHORT_POSITION
        elif CLOSE_SHORT_POSITION in orders or CLOSE_LONG_POSITION in orders:
            self.state = NO_POSITION
