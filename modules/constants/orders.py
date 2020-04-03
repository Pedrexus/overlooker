from functools import total_ordering

from modules.constants import Constant


# @total_ordering
class Order(Constant):
      pass


HOLD_POSITION = Order('HOLD_POSITION')

OPEN_SHORT_POSITION = Order('OPEN_SHORT_POSITION')
CLOSE_SHORT_POSITION = Order('CLOSE_SHORT_POSITION')

OPEN_LONG_POSITION = Order('OPEN_LONG_POSITION')
CLOSE_LONG_POSITION = Order('CLOSE_LONG_POSITION')
