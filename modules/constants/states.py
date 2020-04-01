from modules.constants import Constant


class State(Constant):
	pass

NO_POSITION = State('NO_POSITION')
SHORT_POSITION = State('SHORT_POSITION')
LONG_POSITION = State('LONG_POSITION')
