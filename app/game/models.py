import random
import re
from datetime import datetime

from app import db
import app.game.constants as constants
from app.game.functions import CachedClassProperty, CachedClassFunction
from app.users.models import User


class Card:
    @staticmethod
    def how_many_cards_per_value(value):
        if value == 1:
            return 3
        elif value == 5:
            return 1
        else:
            return 2

    @staticmethod
    def color_to_string(color):
        if color == constants.COLOR_BLUE:
            return "blue"
        elif color == constants.COLOR_GREEN:
            return "green"
        elif color == constants.COLOR_WHITE:
            return "white"
        elif color == constants.COLOR_RED:
            return "red"
        elif color == constants.COLOR_YELLOW:
            return "yellow"
        else:
            raise KeyError(color)

    @staticmethod
    def from_string(card_string):
        color = int(card_string[0])
        value = int(card_string[1])
        uniqueness_value = int(card_string[2])
        new_card = Card(color, value, uniqueness_value)

        return new_card

    def __init__(self, color, value, uniqueness_value):
        self._color = int(color)
        self._value = int(value)
        self._uniqueness_value = int(uniqueness_value)

        assert self._color in constants.COLORS
        assert self._value in constants.VALUES

        assert self._uniqueness_value in range(Card.how_many_cards_per_value(self._value))

    @property
    def color(self):
        return self._color

    @property
    def value(self):
        return self._value

    @property
    def uniqueness_value(self):
        return self._uniqueness_value

    @CachedClassProperty()
    def color_string(self):
        return self.color_to_string(self.color)

    @CachedClassFunction()
    def __str__(self):
        return "{self.color}{self.value}{self.uniqueness_value}".format(self=self)

    @CachedClassFunction()
    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Card):
            return (self.value == other.value and self.color == other.color and
                    self.uniqueness_value == other.uniqueness_value)
        else:
            return self == Card.from_string(str(other))

    def __lt__(self, other):
        return str(self) <= str(other)


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

    state = db.Column(db.Integer(), nullable=False, default=constants.GAME_CREATED)

    @staticmethod
    def card_can_generate_hint(card):
        return card.value == 5

    @staticmethod
    def get_start_number_of_cards_for_players(player_number):
        # TODO
        if player_number == 2:
            return 5
        if player_number == 3:
            return 4
        if player_number == 4:
            return 4
        else:
            raise AttributeError("Invalid number of players.")

    @staticmethod
    def get_random_start_deck():
        all_cards = []

        for color in constants.COLORS:
            for value in constants.VALUES:
                for uniqueness_value in range(Card.how_many_cards_per_value(value)):
                    all_cards.append(Card(color, value, uniqueness_value))

        random.shuffle(all_cards)

        return all_cards

    def __init__(self, start_deck, users, start_player, start_failures, start_hints, start_number_of_cards):
        self.start_failures = start_failures
        self.start_hints = start_hints
        self.start_player = start_player
        self.start_number_of_cards = start_number_of_cards

        for user in users:
            self.to_users.append(UsersInGames(self, user))

        self._start_deck = ",".join(map(str, start_deck))

    @CachedClassProperty()
    def current_turn_number(self):
        return Turn.query.filter_by(game=self).count()

    @property
    def state_string(self):
        if self.state == constants.GAME_LOST:
            return "lost"
        elif self.state == constants.GAME_STARTED:
            return "started"
        elif self.state == constants.GAME_WON:
            return "won"
        elif self.state == constants.GAME_CREATED:
            return "created"
        else:
            raise ValueError("Invalid game state.")

    @CachedClassProperty()
    def users(self):
        return [relation.user for relation in self.to_users]

    @CachedClassProperty()
    def start_deck(self):
        return [Card.from_string(card_string) for card_string in self._start_deck.split(",")]

    @CachedClassProperty()
    def played_turns(self):
        return Turn.query.filter_by(game=self).all()

    @CachedClassProperty()
    def current_user(self):
        users = self.users
        return users[self.current_turn_number % len(users)]

    @CachedClassProperty()
    def current_number_of_failures(self):
        number_of_failures = self.start_failures
        number_of_failures -= Turn.query.filter_by(game=self, type=constants.TURN_PUT, put_correct=False).count()

        return number_of_failures

    @CachedClassProperty()
    def current_number_of_hints(self):
        number_of_hints = self.start_hints
        number_of_hints += Turn.query.filter_by(game=self, hint_restored=True).count()
        number_of_hints -= Turn.query.filter_by(game=self, type=constants.TURN_HINT).count()

        return number_of_hints

    @CachedClassProperty()
    def next_card(self):
        # Startup: everyone needs cards...
        card_counter = len(self.users) * self.start_number_of_cards

        # Every put or destroy leads to a new card...
        turns = filter(lambda turn: turn.type in [constants.TURN_PUT, constants.TURN_DESTROY], self.played_turns)
        card_counter += len(list(turns))

        if card_counter > len(self.start_deck) - 1:
            return None
        else:
            return self.start_deck[card_counter]

    @CachedClassProperty()
    def card_status(self):
        """
        Return the current status of the played card as a dictionary
        color -> last played value. Does only look into the turns,
        that are already on the database.
        """
        card_status = {color: 0 for color in constants.COLORS}

        for turn in self.played_turns:
            if turn.put_correct:
                played_card = turn.cards[0]
                card_status[played_card.color] = played_card.value

        return card_status

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

    def card_fits_good(self, card):
        card_status = self.card_status

        return card_status[card.color] == card.value - 1

    def get_hints_for_card(self, card):
        all_hints = Turn.query.filter_by(game=self, type=constants.TURN_HINT).all()

        # Exactly 4 slots: Hint for value, hint for color, hint for not value, hint for not color
        return_hints = ["", "", "", ""]

        filtered_hints = list(filter(lambda h: card in h.cards, all_hints))
        for hint in filtered_hints:
            if hint.hint_type == constants.HINT_VALUE:
                return_hints[0] = "Value is " + str(hint.hint_value)
            elif hint.hint_type == constants.HINT_COLOR:
                return_hints[1] = "Color is " + Card.color_to_string(hint.hint_color)
            elif hint.hint_type in constants.HINT_NOT_VALUE.values():
                if not return_hints[3]:
                    return_hints[2] = "Value is not "
                else:
                    return_hints[2] += " or "
                return_hints[2] += str(hint.hint_value)
            elif hint.hint_type in constants.HINT_NOT_COLOR.values():
                if not return_hints[3]:
                    return_hints[3] = "Color is not "
                else:
                    return_hints[3] += " or "

                return_hints[3] += Card.color_to_string(hint.hint_color)

        return return_hints

    @CachedClassFunction()
    def get_cards_of_user(self, user):
        start_deck = self.start_deck
        card_counter = 0

        cards_of_user = []

        # First, give the start cards to the user
        user_index = self.users.index(user)
        for counter in range(self.start_number_of_cards):
            cards_of_user.append(start_deck[len(self.users) * counter + user_index])

        card_counter += self.start_number_of_cards * len(self.users)

        # Then check every other turns: if it is a put or destroy term, the given card is deleted from the user and
        # he will get the next one. If the user is not involved, remember to still keep on counting cards.
        turns = list(filter(lambda turn: turn.type in [constants.TURN_PUT, constants.TURN_DESTROY], self.played_turns))

        for turn in turns:
            if turn.user == user:
                assert len(turn.cards) == 1

                del cards_of_user[cards_of_user.index(turn.cards[0])]

                # here we allow the users to go on playing even if there are no more cards (which is possible)
                if card_counter < len(start_deck):
                    cards_of_user.append(start_deck[card_counter])

            card_counter += 1

        return cards_of_user

    @CachedClassFunction()
    def get_possible_turns(self, user):
        possible_turns = []

        current_turn_number = self.current_turn_number

        # Making turns downs only make sense if the game is running
        if self.state != constants.GAME_STARTED:
            return possible_turns

        # Comment: we do not test for the current user as it may be needed to show the hints also for other players.

        # Putting down cards is only possible for the cards the user owns
        # Destroying a card is only possible for the cards the user owns
        for card in self.get_cards_of_user(user):
            put_turn = PossibleTurn(self, user, constants.TURN_PUT, current_turn_number, len(possible_turns))
            put_turn.cards = card

            possible_turns.append(put_turn)

            destroy_turn = PossibleTurn(self, user, constants.TURN_DESTROY, current_turn_number, len(possible_turns))
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
                other_users_cards = self.get_cards_of_user(other_user)
                for color in constants.COLORS:
                    cards_with_this_color = list(
                        filter(lambda card: card.color == color, other_users_cards))

                    turn = PossibleTurn(self, user, constants.TURN_HINT, current_turn_number, len(possible_turns))
                    turn.hint_user = other_user

                    if cards_with_this_color:
                        turn.cards = cards_with_this_color
                        turn.hint_type = constants.HINT_COLOR
                    else:
                        turn.cards = other_users_cards
                        turn.hint_type = constants.HINT_NOT_COLOR[color]

                    possible_turns.append(turn)

                # (c) A value hint, (d) A not-value hint
                for value in constants.VALUES:
                    cards_with_this_value = list(filter(lambda card: card.value == value,
                                                        other_users_cards))

                    turn = PossibleTurn(self, user, constants.TURN_HINT, current_turn_number, len(possible_turns))
                    turn.hint_user = other_user

                    if cards_with_this_value:
                        turn.cards = cards_with_this_value
                        turn.hint_type = constants.HINT_VALUE
                    else:
                        turn.cards = other_users_cards
                        turn.hint_type = constants.HINT_NOT_VALUE[value]

                    possible_turns.append(turn)

        for turn in possible_turns:
            turn.set_turn_properties()

        return possible_turns


class TurnBaseObject:
    @property
    def cards(self):
        if self._card is None or self._card == "":
            return []
        return [Card.from_string(card) for card in self._card.split(",")]

    @cards.setter
    def cards(self, card_or_cards):
        if isinstance(card_or_cards, Card):
            card_or_cards = [card_or_cards]

        self._card = ",".join(map(str, card_or_cards))

    @property
    def type_string(self):
        if self.type == constants.TURN_DESTROY:
            return "destroy"
        elif self.type == constants.TURN_HINT:
            return "hint"
        elif self.type == constants.TURN_PUT:
            return "put"
        else:
            raise ValueError("Invalid turn type.")

    @CachedClassProperty()
    def hint_type_string(self):
        # FIXME
        for constant in dir(constants):
            if constant.startswith("HINT_") and getattr(constants, constant) == self.hint_type:
                return constant

        for name, constant in constants.HINT_NOT_COLOR.items():
            if constant == self.hint_type:
                return "HINT_NOT_COLOR " + str(name)

        for name, constant in constants.HINT_NOT_VALUE.items():
            if constant == self.hint_type:
                return "HINT_NOT_VALUE " + str(name)

        raise ValueError("Invalid hint type.")

    @CachedClassProperty()
    def hint_value(self):
        assert self.type == constants.TURN_HINT

        if self.hint_type == constants.HINT_VALUE:
            return self.cards[0].value
        for value, constant in constants.HINT_NOT_VALUE.items():
            if constant == self.hint_type:
                return value
        raise ValueError()

    @CachedClassProperty()
    def hint_color(self):
        assert self.type == constants.TURN_HINT
        if self.hint_type == constants.HINT_COLOR:
            return self.cards[0].color
        for color, constant in constants.HINT_NOT_COLOR.items():
            if constant == self.hint_type:
                return color
        raise ValueError()

    @CachedClassFunction()
    def __str__(self):
        msg = "{self.user.name}, {self.turn_number}: {self.type_string}"
        if self.type in [constants.TURN_DESTROY, constants.TURN_PUT]:
            msg += " of {self.cards}"
        elif self.type == constants.TURN_HINT:
            msg += " {self.hint_type_string} to {self.hint_user.name} ({self.cards})"

        msg += " last: {self.last_card_drawn}, put: {self.put_correct}, hint: {self.hint_restored}"

        return msg.format(self=self)

    @CachedClassFunction()
    def __repr__(self):
        return str(self)


class Turn(db.Model, TurnBaseObject):
    __tablename__ = "turns"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer, nullable=False)

    _user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User, backref=db.backref("turns_played", uselist=True, cascade='delete,all'),
                           foreign_keys=[_user_id])

    _game_id = db.Column(db.Integer, db.ForeignKey(Game.id), nullable=False)
    game = db.relationship(Game, backref=db.backref("turns_in_game", uselist=True, cascade='delete,all'))
    turn_number = db.Column(db.Integer, nullable=False)

    _card = db.Column(db.String(100), nullable=False, default="")
    hint_type = db.Column(db.Integer, nullable=False, default=-1)

    _hint_user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    hint_user = db.relationship(User, backref=db.backref("hints_given", uselist=True, cascade='delete,all'),
                                foreign_keys=[_hint_user_id])

    last_card_drawn = db.Column(db.Boolean, nullable=False, default=False)
    put_correct = db.Column(db.Boolean, nullable=False, default=False)
    hint_restored = db.Column(db.Boolean, nullable=False, default=False)

    @staticmethod
    def from_possible_turn(possible_turn):
        new_turn = Turn()

        new_turn.type = possible_turn.type
        new_turn.user = possible_turn.user
        new_turn.game = possible_turn.game
        new_turn.turn_number = possible_turn.turn_number
        new_turn._card = possible_turn._card
        new_turn.hint_type = possible_turn.hint_type
        new_turn.hint_user = possible_turn.hint_user
        new_turn.last_card_drawn = possible_turn.last_card_drawn
        new_turn.put_correct = possible_turn.put_correct
        new_turn.hint_restored = possible_turn.hint_restored

        return new_turn


class PossibleTurn(TurnBaseObject):
    def __init__(self, game, user, turn_type, turn_number, possibility_number):
        self.game = game
        self.type = turn_type
        self.user = user
        self.turn_number = turn_number
        self.possibility_number = possibility_number

        self._card = ""

        self.last_card_drawn = False
        self.hint_restored = False
        self.put_correct = False

        self.hint_type = -1

        self.hint_user = None

    @CachedClassProperty()
    def turn_string(self):
        if self.type == constants.TURN_DESTROY:
            return "Destroy card"
        elif self.type == constants.TURN_PUT:
            return "Put card down"
        elif self.type == constants.TURN_HINT:
            if self.hint_type == constants.HINT_COLOR:
                hint_string = "You have a " + Card.color_to_string(self.hint_color) + " card"
            elif self.hint_type == constants.HINT_VALUE:
                hint_string = "You have a " + str(self.hint_value)
            elif self.hint_type in constants.HINT_NOT_COLOR.values():
                hint_string = "You do not have a " + Card.color_to_string(self.hint_color) + " card"
            elif self.hint_type in constants.HINT_NOT_VALUE.values():
                hint_string = "You do not have a " + str(self.hint_value)
            else:
                raise ValueError("Invalid hint: " + str(self.hint_type))

            return "Give hint: " + hint_string
        else:
            raise ValueError("Invalid turn type.")

    def set_turn_properties(self):
        game = self.game

        if game.next_card is None:
            self.last_card_drawn = True

        if self.type == constants.TURN_DESTROY:
            if game.current_number_of_hints < game.start_hints:
                self.hint_restored = True
        elif self.type == constants.TURN_PUT:
            if game.card_fits_good(self.cards[0]):
                self.put_correct = True
                if game.card_can_generate_hint(self.cards[0]):
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
