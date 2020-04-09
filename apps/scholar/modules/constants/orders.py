from . import Constant


# @total_ordering
class Order(Constant):
    pass


HOLD_POSITION = Order('HOLD POSITION')
END_POSITION = Order('END POSITION')

OPEN_SHORT_POSITION = Order('OPEN SHORT POSITION')
CLOSE_SHORT_POSITION = Order('CLOSE SHORT POSITION')

OPEN_LONG_POSITION = Order('OPEN LONG POSITION')
CLOSE_LONG_POSITION = Order('CLOSE LONG POSITION')
