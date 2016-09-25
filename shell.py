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

    if os.path.exists("app.db"):
        os.unlink("app.db")

    create_db()

    user = User(u"test", "test@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
    db.session.add(user)
    db.session.commit()

    os.environ['PYTHONINSPECT'] = 'True'
