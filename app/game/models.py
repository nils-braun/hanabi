from datetime import datetime

from app import db
import app.game.constants as constants


class Card:
    def __init__(self, value, color):
        self.value = value
        self.color = color

        assert self.color in constants.COLORS

    def __str__(self):
        return "C{color}#{value}".format(color=self.color, value=self.value)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(250), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    _start_deck = db.Column(db.String(2000), nullable=False) # TODO: Length
    started = db.Column(db.DateTime, nullable=False, default=datetime.now())
    start_failures = db.Column(db.Integer, nullable=False)
    start_hints = db.Column(db.Integer, nullable=False)

    _start_player_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    start_player = db.relationship(User, backref=db.backref("games_started", uselist=True, cascade='delete,all'))

    state = db.Column(db.Integer(), nullable=False, default=-1)

    def __init__(self, start_deck, start_player, start_failures, start_hints):
        self.start_deck = start_deck
        self.start_failures = start_failures
        self.start_hints = start_hints
        self.start_player = start_player


    @property
    def start_deck(self) -> list(Card):
        return [Card.from_string(card_string) for card_string in self._start_deck.split(",")]

    @start_deck.setter
    def start_deck(self, start_deck: list(Card)) -> None:
        self._start_deck = ",".join(start_deck)


    @property
    def users(self) -> list(User):
        return [relation.user for relation in self.to_users]

    @users.setter
    def users(self, users: list(User)) -> None:
        for user in users:
            self.to_users.append(UsersInGames(self, user))


    @staticmethod
    def card_can_generate_hint(card: Card) -> bool:
        return card.value == 5

    def card_fits_good(self, card: Card) -> bool:
        card_status = self.card_status

        return card_status[card.color] == card.value - 1


    @property
    def current_turn_number(self) -> int:
        return self.get_turns().count()

    @property
    def played_turns(self) -> list(Turn):
        return Turn.query.filter_by(game=self)

    @property
    def current_number_of_hints(self) -> int:
        number_of_hints = self.start_hints
        number_of_hints += Turn.query.filter_by(game=self, hint_restored=True).count()
        number_of_hints -= Turn.query.filter_by(game=self, type=constants.TURN_HINT).count()

        return number_of_hints

    @property
    def card_status(self) -> {int: int}:
        """
        Return the current status of the played card as a dictionary
        color -> last played value. Does only look into the turns,
        that are already on the database.
        """
        card_status = {color: 0 for color in constants.COLORS}

        for turn in self.get_turns():
            if turn.put_correct:
                played_card = turn.card
                card_status[played_card.color] = played_card.value

        return card_status


class Turn(db.Model):
    __tablename__ = "turns"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer, nullable=False)

    _user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User, backref=db.backref("turns_played", uselist=True, cascade='delete,all'), foreign_keys=[_user_id])

    _game_id = db.Column(db.Integer, db.ForeignKey(Game.id), nullable=False)
    game = db.relationship(Game, backref=db.backref("turns_in_game", uselist=True, cascade='delete,all'))
    turn_number = db.Column(db.Integer, nullable=False)

    put_correct = db.Column(db.Boolean, nullable=False, default=True)
    hint_restored = db.Column(db.Boolean, nullable=False, default=False)
    card = db.Column(db.String(100), nullable=False)
    hint_type = db.Column(db.Integer, nullable=False, default=-1)

    _hint_user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    hint_user = db.relationship(User, backref=db.backref("hints_given", uselist=True, cascade='delete,all'), foreign_keys=[_hint_user_id])

    def set_turn_properties(self):
        game = self.game
        if self.type == constants.TURN_DESTROY:
            if game.get_current_number_of_hints() < game.start_hints:
                self.hint_restored = True
        elif self.type == constants.TURN_PUT:
            if game.card_fits_good(self.card):
                self.put_correct = True
                if game.card_can_generate_hint(self.card):
                    self.hint_restored = True


class UsersInGames(db.Model):
    __tablename__ = "users_to_games"
    _game_id = db.Column(db.Integer, db.ForeignKey(Game.id), primary_key=True)
    _user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)

    game = db.relationship(Game, backref=db.backref("to_users", uselist=True, cascade="delete,all"))
    user = db.relationship(User, backref=db.backref("to_games", uselist=True, cascade="delete,all"))

    def __init__(self, game, user):
        self.user = user
        self.game = game