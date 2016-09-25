from unittest import main

import app.game.constants as constants
from app import db
from app.game.functions import make_turn
from app.game.models import User, Turn
from app.game.tests.fixtures import DatabaseTest


class TestMakeTurnCornerCases(DatabaseTest):
    def test_make_turn_no_game(self):
        # Game has to be set
        turn = Turn(None, None, None, 0)
        self.assertRaisesRegex(AttributeError, "No game assigned to the turn.", make_turn, turn)

    def test_make_turn_no_user(self):
        # User has to be in the game
        other_user = User("other_user")
        db.session.add(other_user)
        db.session.commit()

        turn = Turn(self.game, other_user, constants.TURN_DESTROY, 0)

        self.assertRaisesRegex(AttributeError, "It is not the users turn.", make_turn, turn)

    def test_make_turn_stopped_game(self):
        # Game is still running
        turn = Turn(self.game, self.user, constants.TURN_DESTROY, 0)

        self.game.state = constants.GAME_LOST
        db.session.merge(self.game)

        self.assertRaisesRegex(RuntimeError, "Turn is not possible.", make_turn, turn)

    def test_game_properties(self):
        self.assertEqual(self.game.current_number_of_hints, 10)

    def test_turn_number_correct(self):
        # Turn number is correct
        turn = Turn(self.game, self.user, constants.TURN_DESTROY, 0)

        self.assertEqual(self.game.current_turn_number, 0)

        turn.turn_number = 1
        self.assertRaisesRegex(RuntimeError, "Turn is not possible.", make_turn, turn)