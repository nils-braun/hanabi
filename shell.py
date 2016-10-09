#!/usr/bin/env python
import os
from pprint import pprint

from flask import *
from app import *
from app.game.models import User, Turn, Game


def create_db():
    """
    Convenience function to create the db file with all needed tables.
    """
    db.create_all()


if __name__ == '__main__':
    print("Type create_db() to create the DB.")

    def create_db():

        if os.path.exists("app.db"):
            os.unlink("app.db")

        db.create_all()

        user = User(u"test", "test@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
        db.session.add(user)

        user_2 = User(u"test2", "test2@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
        db.session.add(user_2)
        db.session.commit()

        start_deck = Game.get_random_start_deck()

        start_player = User.query.filter_by(name="test").one()
        users = [User.query.filter_by(name=user_name.strip()).one() for user_name in ["test", "test2"]]

        new_game = Game(start_deck=start_deck, start_player=start_player,
                        users=users,
                        start_failures=3,
                        start_hints=10,
                        start_number_of_cards=Game.get_start_number_of_cards_for_players(len(users)))

        db.session.add(new_game)
        db.session.commit()

    os.environ['PYTHONINSPECT'] = 'True'
