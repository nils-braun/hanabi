from app import db
from app.game.constants import GAME_STARTED, TURN_DESTROY, TURN_PUT
from app.game.models import Turn, Game


def make_turn(turn: Turn):
    game = turn.game
    if not game:
        raise AttributeError("No game assigned to the turn.")

    user = turn.user
    if user not in game.get_users():
        raise AttributeError("User is not in the game.")

    if user != game.current_user():
        raise AttributeError("It is not the users turn.")

    if game.state != GAME_STARTED:
        raise AttributeError("Game is not running.")

    if not game.get_current_turn_number(turn) == turn.turn_number:
        raise AttributeError("Turn number is wrong.")

    if not turn in game.get_possible_turns(user):
        raise RuntimeError("Turn is not possible.")

    turn.set_turn_properties()

    db.session.add(turn)
