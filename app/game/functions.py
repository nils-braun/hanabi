from app import db
from app.game.models import Turn


def make_turn(turn: Turn):
    game = turn.game
    if not game:
        raise AttributeError("No game assigned to the turn.")

    user = turn.user

    if user != game.current_user:
        raise AttributeError("It is not the users turn.")

    if turn not in game.get_possible_turns(user):
        raise RuntimeError("Turn is not possible.")

    turn.set_turn_properties()

    db.session.add(turn)
    # TODO: Do we need a commit here?

    game.update_game_status()
    db.session.merge(game)

    db.session.commit()
