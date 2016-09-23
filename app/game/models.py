import re
from datetime import datetime

from app import db
import app.game.constants as constants


class Card:
    def __init__(self, color, value, uniqueness_value):
        self.color = color
        self.value = value
        self.uniqueness_value = uniqueness_value

        assert self.color in constants.COLORS
        assert self.value in constants.VALUES

        assert self.uniqueness_value in range(Card.how_many_cards_per_value(self.value))

    @staticmethod
    def how_many_cards_per_value(value):
        if value == 1:
            return 3
        elif value == 5:
            return 1
        else:
            return 2

    def __str__(self):
        return "C{color}#{value}#{uniqueness_value}".format(color=self.color, value=self.value,
                                                            uniqueness_value=self.uniqueness_value)

    @staticmethod
    def from_string(card_string):
        regex_decomposition = re.match(r"C([0-9])#([1-5])#([0-4])", card_string)

        assert regex_decomposition

        value = regex_decomposition.group(1)
        color = regex_decomposition.group(2)
        uniqueness_value = regex_decomposition.group(2)
        new_card = Card(color, value, uniqueness_value)

        return new_card


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(250), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    _start_deck = db.Column(db.String(len(constants.COLORS) * 10 * 10), nullable=False)
    started = db.Column(db.DateTime, nullable=False, default=datetime.now())
    start_failures = db.Column(db.Integer, nullable=False)
    start_hints = db.Column(db.Integer, nullable=False)
    start_number_of_cards = db.Column(db.Integer, nullable=False)

    _start_player_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    start_player = db.relationship(User, backref=db.backref("games_started", uselist=True, cascade='delete,all'))

    state = db.Column(db.Integer(), nullable=False, default=-1)

    def __init__(self, start_deck, start_player, start_failures, start_hints):
        self.start_deck = start_deck
        self.start_failures = start_failures
        self.start_hints = start_hints
        self.start_player = start_player

    @staticmethod
    def card_can_generate_hint(card: Card) -> bool:
        return card.value == 5

    def update_game_status(self):
        # the users have lost when they made too many mistakes
        if self.current_number_of_failures < 1:
            self.state = constants.GAME_LOST
            return True

        not_finished_cards = filter(lambda value: value != 5, self.card_status.values())
        if not not_finished_cards:
            self.state = constants.GAME_WON
            return True

        turns_after_last_card = Turn.query.filter_by(game=self, last_card_drawn=True).count()
        if turns_after_last_card > len(self.users):
            self.state = constants.GAME_LOST
            return True

        return False

    def card_fits_good(self, card: Card) -> bool:
        card_status = self.card_status

        return card_status[card.color] == card.value - 1

    def get_cards_of_user(self, user: User) -> list(Card):
        start_deck = self.start_deck
        card_counter = 0

        cards_of_user = []

        # First, give the start cards to the user
        user_index = self.users.index(user)
        for counter in range(self.start_number_of_cards):
            cards_of_user += start_deck[self.start_number_of_cards * counter + user_index]

        card_counter += self.start_number_of_cards * len(self.users)

        # Then check every other turns: if it is a put or destroy term, the given card is deleted from the user and
        # he will get the next one. If the user is not involved, remember to still keep on counting cards.
        turns = filter(lambda turn: turn.type in [constants.TURN_HINT, constants.TURN_DESTROY], self.played_turns)
        for turn in turns:
            if turn.user == user:
                assert len(turn.cards) == 1

                del cards_of_user[cards_of_user.index(turn.cards[0])]

                # here we allow the users o go on playing even if there are no more cards (which is possible)
                if card_counter < len(start_deck):
                    cards_of_user.append(start_deck[card_counter])

            card_counter += 1

            assert card_counter < len(start_deck)

        return cards_of_user

    def get_possible_turns(self, user: User) -> list(Turn):
        possible_turns = []

        # Making turns downs only make sense if the game is running
        if self.state != constants.GAME_STARTED:
            return possible_turns

        # Comment: we do not test for the current user as it may be needed to show the hints also for other players.

        # Putting down cards is only possible for the cards the user owns
        # Destroying a card is only possible for the cards the user owns
        for card in self.get_cards_of_user(user):
            put_turn = Turn(self, constants.TURN_PUT)
            put_turn.cards = card

            possible_turns.append(put_turn)

            destroy_turn = Turn(self, constants.TURN_DESTROY)
            destroy_turn.cards = card

            possible_turns.append(destroy_turn)

        # A hint can only be given if there are hint left
        if self.current_number_of_hints > 0:

            # Giving a hint is only possible to all other users
            for other_user in self.users:
                if other_user == user:
                    continue

                # There are four hint types
                # (a) A color hint, (b) A not-color hint
                for color in constants.COLORS:
                    cards_with_this_color = filter(lambda card: card.color == color, self.get_cards_of_user(other_user))

                    turn = Turn(self, constants.TURN_HINT)
                    turn.hint_user = other_user

                    if cards_with_this_color:
                        turn.cards = cards_with_this_color
                        turn.hint_type = constants.HINT_COLOR
                    else:
                        turn.hint_type = constants.HINT_NOT_COLOR[color]

                    possible_turns.append(turn)

                # (c) A value hint, (d) A not-value hint
                for value in constants.VALUES:
                    cards_with_this_value = filter(lambda card: card.value == value,
                                                   self.get_cards_of_user(other_user))

                    turn = Turn(self, constants.TURN_HINT)
                    turn.hint_user = other_user

                    if cards_with_this_value:
                        turn.cards = cards_with_this_value
                        turn.hint_type = constants.HINT_VALUE
                    else:
                        turn.hint_type = constants.HINT_NOT_VALUE[value]

                    possible_turns.append(turn)

        # Set common attributes
        for turn in possible_turns:
            turn.user = user
            turn.turn_number = self.current_turn_number + 1

        return possible_turns

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


    @property
    def current_turn_number(self) -> int:
        return self.get_turns().count()

    @property
    def played_turns(self) -> list(Turn):
        return Turn.query.filter_by(game=self)

    @property
    def current_number_of_hints(self) -> int:
        number_of_hints = self.start_failures
        number_of_hints -= Turn.query.filter_by(game=self, type=constants.TURN_PUT, put_correct=False).count()

        return number_of_hints

    @property
    def current_number_of_hints(self) -> int:
        number_of_hints = self.start_hints
        number_of_hints += Turn.query.filter_by(game=self, hint_restored=True).count()
        number_of_hints -= Turn.query.filter_by(game=self, type=constants.TURN_HINT).count()

        return number_of_hints

    @property
    def next_card(self):
        # Startup: everyone needs cards...
        card_counter = len(self.users) * self.start_number_of_cards

        # Every put or destroy leads to a new card...
        turns = filter(lambda turn: turn.type in [constants.TURN_HINT, constants.TURN_DESTROY], self.played_turns)
        card_counter += len(list(turns))

        if card_counter > len(self.start_deck) - 1:
            return None
        else:
            return self.start_deck[card_counter]

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
                played_card = turn.cards
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

    _card = db.Column(db.String(100), nullable=False)
    hint_type = db.Column(db.Integer, nullable=False, default=-1)

    _hint_user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    hint_user = db.relationship(User, backref=db.backref("hints_given", uselist=True, cascade='delete,all'), foreign_keys=[_hint_user_id])

    last_card_drawn = db.Column(db.Boolean, nullable=False, default=False)
    put_correct = db.Column(db.Boolean, nullable=False, default=False)
    hint_restored = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, game, type):
        self.game = game
        self.type = type

    @property
    def cards(self):
        return [Card.from_string(card) for card in self._card.split(",")]

    @cards.setter
    def cards(self, card_or_cards):
        if isinstance(Card, card_or_cards):
            card_or_cards = [card_or_cards]

        self._card = ",".join(card_or_cards)

    def set_turn_properties(self):
        game = self.game

        if game.next_card is None:
            self.last_card_drawn = True

        if self.type == constants.TURN_DESTROY:
            if game.current_number_of_hints < game.start_hints:
                self.hint_restored = True
        elif self.type == constants.TURN_PUT:
            if game.card_fits_good(self.cards):
                self.put_correct = True
                if game.card_can_generate_hint(self.cards):
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