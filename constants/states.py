from functools import total_ordering

from .constant import Constant


@total_ordering
class State(Constant):

    def __init__(self, value, *args, **kwargs):
        super(State, self).__init__(*args, **kwargs)
        self.value = value

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.value == other

    def __lt__(self, other):
        return self.value < other

    def __sub__(self, other):
        return self.value - other

    def __rsub__(self, other):
        return other - self.value


NO_POSITION = State(0, 'NO POSITION')
SHORT_POSITION = State(-1, 'SHORT POSITION')
LONG_POSITION = State(1, 'LONG POSITION')
