from unittest import TestCase

from app import db
from app.game import constants
from app.game.models import Game, Card, Turn, UsersInGames
from app.game.tests.fixtures import DatabaseTest


class TestGame(DatabaseTest):
    def test_card_can_generate_hint(self):
        test_card = Card(constants.COLOR_BLUE, 1, 0)
        self.assertFalse(Game.card_can_generate_hint(test_card))

        test_card = Card(constants.COLOR_BLUE, 5, 0)
        self.assertTrue(Game.card_can_generate_hint(test_card))

    def test_update_game_status(self):
        self.fail()

    def test_card_fits_good(self):
        test_card = Card(constants.COLOR_RED, 2, 0)
        self.assertFalse(self.game.card_fits_good(test_card))

        test_card = Card(constants.COLOR_BLUE, 1, 0)
        self.assertTrue(self.game.card_fits_good(test_card))

        # Added turn, but turn is makes as not correct
        turn = Turn(self.game, self.user, constants.TURN_PUT, 0)
        test_card = Card(constants.COLOR_BLUE, 1, 0)
        turn.cards = [test_card]
        db.session.add(turn)
        db.session.commit()

        test_card = Card(constants.COLOR_BLUE, 2, 0)
        self.assertFalse(self.game.card_fits_good(test_card))

        # Make turn marked as correct
        turn.put_correct = True
        db.session.merge(turn)
        db.session.commit()

        test_card = Card(constants.COLOR_BLUE, 2, 0)
        self.assertTrue(self.game.card_fits_good(test_card))

        test_card = Card(constants.COLOR_RED, 2, 1)
        self.assertFalse(self.game.card_fits_good(test_card))

        # Last card is played
        for i in range(1, 6):
            turn = Turn(self.game, self.user, constants.TURN_PUT, 1 + i)
            test_card = Card(constants.COLOR_RED, i, 0)
            turn.cards = [test_card]
            turn.put_correct = True
            db.session.add(turn)

        db.session.commit()

        for i in range(1, 6):
            test_card = Card(constants.COLOR_RED, i, 0)
            self.assertFalse(self.game.card_fits_good(test_card))

    def test_get_cards_of_user(self):
        cards_of_user_1 = self.game.get_cards_of_user(self.user)
        cards_of_user_2 = self.game.get_cards_of_user(self.user_2)

        self.assertEqual(cards_of_user_1, ["C0#1#0"])
        self.assertEqual(cards_of_user_2, ["C1#1#0"])

        # User 1 makes a hint turn => nothing should change
        turn = Turn(self.game, self.user, constants.TURN_HINT, 0)
        db.session.add(turn)
        db.session.commit()

        cards_of_user_1 = self.game.get_cards_of_user(self.user)
        cards_of_user_2 = self.game.get_cards_of_user(self.user_2)

        self.assertEqual(cards_of_user_1, ["C0#1#0"])
        self.assertEqual(cards_of_user_2, ["C1#1#0"])

        # User 2 makes a put turn => he will get a new card
        turn = Turn(self.game, self.user_2, constants.TURN_PUT, 0)
        turn.cards = ["C1#1#0"]
        db.session.add(turn)
        db.session.commit()

        cards_of_user_1 = self.game.get_cards_of_user(self.user)
        cards_of_user_2 = self.game.get_cards_of_user(self.user_2)

        self.assertEqual(cards_of_user_1, ["C0#1#0"])
        self.assertEqual(cards_of_user_2, ["C2#1#0"])

        # User 1 makes a destroy turn => he will get a new card
        turn = Turn(self.game, self.user, constants.TURN_DESTROY, 0)
        turn.cards = ["C0#1#0"]
        db.session.add(turn)
        db.session.commit()

        cards_of_user_1 = self.game.get_cards_of_user(self.user)
        cards_of_user_2 = self.game.get_cards_of_user(self.user_2)

        self.assertEqual(cards_of_user_1, ["C0#1#1"])
        self.assertEqual(cards_of_user_2, ["C2#1#0"])

        # User 2 makes another destroy turn => there are no mor cards left
        turn = Turn(self.game, self.user_2, constants.TURN_DESTROY, 0)
        turn.cards = ["C2#1#0"]
        db.session.add(turn)
        db.session.commit()

        cards_of_user_1 = self.game.get_cards_of_user(self.user)
        cards_of_user_2 = self.game.get_cards_of_user(self.user_2)

        self.assertEqual(cards_of_user_1, ["C0#1#1"])
        self.assertEqual(cards_of_user_2, [])

    def test_get_possible_turns(self):
        self.fail()

    def test_start_deck(self):
        self.assertEqual(self.game.start_deck, self.start_deck)

    def test_users(self):
        self.assertEqual(self.game.users, [self.user, self.user_2])

        users_in_game = UsersInGames.query.all()
        self.assertEqual(len(users_in_game), 2)
        self.assertEqual(users_in_game[0].user, self.user)
        self.assertEqual(users_in_game[0].game, self.game)
        self.assertEqual(users_in_game[1].user, self.user_2)
        self.assertEqual(users_in_game[1].game, self.game)

    def test_current_user_and_turn_number(self):
        self.assertEqual(self.game.current_user, self.user)
        self.assertEqual(self.game.current_turn_number, 0)
        self.assertEqual(self.game.played_turns.all(), [])

        # Add a turn, which one does not matter
        turn_1 = Turn(self.game, self.user, constants.TURN_PUT, 0)
        db.session.add(turn_1)
        db.session.commit()

        self.assertEqual(self.game.current_user, self.user_2)
        self.assertEqual(self.game.current_turn_number, 1)
        self.assertEqual(self.game.played_turns.all(), [turn_1])

        # Add a turn, which one does not matter
        turn_2 = Turn(self.game, self.user_2, constants.TURN_PUT, 1)
        db.session.add(turn_2)
        db.session.commit()

        self.assertEqual(self.game.current_user, self.user)
        self.assertEqual(self.game.current_turn_number, 2)
        self.assertEqual(self.game.played_turns.all(), [turn_1, turn_2])

    def test_current_number_of_hints(self):
        self.assertEqual(self.game.current_number_of_hints, 10)

        # Add a hint turn
        turn = Turn(self.game, self.user, constants.TURN_HINT, 0)
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.current_number_of_hints, 9)

        # Add a hint-restore turn
        turn = Turn(self.game, self.user, constants.TURN_DESTROY, 0)
        turn.hint_restored = True
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.current_number_of_hints, 10)

    def test_current_number_of_failures(self):
        self.assertEqual(self.game.current_number_of_failures, 3)

        # Add a correct put turn
        turn = Turn(self.game, self.user, constants.TURN_PUT, 0)
        turn.put_correct = True
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.current_number_of_failures, 3)

        # Add a wrong put turn
        turn = Turn(self.game, self.user, constants.TURN_PUT, 0)
        turn.put_correct = False
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.current_number_of_failures, 2)

        # All other turns should not change the number
        turn = Turn(self.game, self.user, constants.TURN_DESTROY, 0)
        # this property should not make a difference!
        turn.put_correct = False
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.current_number_of_failures, 2)

    def test_next_card(self):
        self.assertEqual(self.game.next_card, self.start_deck[2])
        self.assertEqual(self.game.next_card, "C2#1#0")

        # Giving a hint should not change the cards
        turn = Turn(self.game, self.user, constants.TURN_HINT, 0)
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.next_card, self.start_deck[2])
        self.assertEqual(self.game.next_card, "C2#1#0")

        # A destroy and a put however lead to a new card
        turn = Turn(self.game, self.user, constants.TURN_DESTROY, 0)
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.next_card, self.start_deck[3])
        self.assertEqual(self.game.next_card, "C0#1#1")

        # After the last card is played, there is no card left
        turn = Turn(self.game, self.user, constants.TURN_PUT, 0)
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.next_card, None)

        # and it does not matter how many cards are played
        turn = Turn(self.game, self.user, constants.TURN_PUT, 0)
        db.session.add(turn)
        db.session.commit()

        self.assertEqual(self.game.next_card, None)

    def test_card_status(self):
        card_status = self.game.card_status

        for color in constants.COLORS:
            self.assertEqual(card_status[color], 0)

        # Add a correct put
        turn = Turn(self.game, self.user, constants.TURN_PUT, 0)
        test_card = Card(constants.COLOR_BLUE, 1, 0)
        turn.cards = [test_card]
        turn.put_correct = True
        db.session.add(turn)
        db.session.commit()

        card_status = self.game.card_status

        for color in constants.COLORS:
            if color == constants.COLOR_BLUE:
                self.assertEqual(card_status[color], 1)
            else:
                self.assertEqual(card_status[color], 0)
