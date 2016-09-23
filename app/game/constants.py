GAME_CREATED = 0
GAME_STARTED = 1
GAME_FINISHED = 2

TURN_PUT = 0
TURN_DESTROY = 1
TURN_HINT = 2

COLOR_GREEN = 0
COLOR_BLUE = 1
COLOR_WHITE = 2
COLOR_RED = 3
COLOR_YELLOW = 4

COLORS = [COLOR_GREEN, COLOR_BLUE, COLOR_WHITE, COLOR_YELLOW, COLOR_RED]

VALUES = range(1, 6)

HINT_COLOR = 1
HINT_VALUE = 2
HINT_NOT_COLOR = {COLOR_GREEN: 10, COLOR_BLUE: 11, COLOR_WHITE: 12, COLOR_YELLOW: 13, COLOR_RED: 14}
HINT_NOT_VALUE = {COLOR_GREEN: 20, COLOR_BLUE: 21, COLOR_WHITE: 22, COLOR_YELLOW: 23, COLOR_RED: 24}