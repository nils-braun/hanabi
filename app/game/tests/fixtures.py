from unittest import TestCase

from app import db
from app.game import constants as constants
from app.game.models import User, Game


class DatabaseTest(TestCase):
    def setUp(self):
        db.create_all()

        self.user = User("test")
        db.session.add(self.user)
        self.user_2 = User("test_2")
        db.session.add(self.user_2)

        self.start_deck = ["C0#1#0", "C1#1#0", "C2#1#0", "C0#1#1"]
        self.game = Game(self.start_deck, self.user, 3, 10, 1)
        self.game.users = [self.user, self.user_2]
        self.game.state = constants.GAME_STARTED

        db.session.add(self.game)
        db.session.commit()

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()