import app.game.constants as constants
from app.game.models import Turn, Game, Card
from app.game.tests.fixtures import DatabaseTest


class TestTurn(DatabaseTest):
    def test_cards(self):
        turn = Turn(self.game, self.user, constants.TURN_HINT, 0)

        self.assertEqual(turn.cards, [])

        turn.cards = ["C0#1#0", "C2#3#1"]

        self.assertEqual(turn.cards, [Card.from_string("C0#1#0"),
                                      Card.from_string("C2#3#1")])

        self.assertEqual(turn.cards[0].color, 0)
        self.assertEqual(turn.cards[0].value, 1)
        self.assertEqual(turn.cards[0].uniqueness_value, 0)
        self.assertEqual(turn.cards[1].color, 2)
        self.assertEqual(turn.cards[1].value, 3)
        self.assertEqual(turn.cards[1].uniqueness_value, 1)

    def test_set_turn_properties(self):
        self.fail()
