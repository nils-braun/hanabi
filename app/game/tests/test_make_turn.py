import os
from unittest import TestCase, main

from app import db
import app.game.constants as constants
from app.game.functions import make_turn
from app.game.models import Game, User, Turn


class DatabaseTest(TestCase):
    def setUp(self):
        db.create_all()

        self.user = User("test")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()


class TestMakeTurnCornerCases(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)

        self.game = Game(["C0#1#0", "C1#1#0", "C2#1#0", "C0#1#1"], self.user, 3, 10, 4)
        self.game.users = [self.user]
        self.game.state = constants.GAME_STARTED

        db.session.add(self.game)
        db.session.commit()


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


if __name__ == '__main__':
    main()