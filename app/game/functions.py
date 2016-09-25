from app import db


def make_turn(turn_id, game, user):
    if user != game.current_user:
        raise AttributeError("It is not the users turn.")

    possible_turns = game.get_possible_turns(user)

    if turn_id >= len(possible_turns):
        raise RuntimeError("Turn is not possible.")

    turn = possible_turns[turn_id]
    turn.set_turn_properties()

    db.session.add(turn)
    # TODO: Do we need a commit here?

    game.update_game_status()
    db.session.merge(game)

    db.session.commit()
