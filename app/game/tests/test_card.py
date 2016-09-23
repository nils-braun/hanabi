from unittest import TestCase

from app.game.models import Card


class TestCard(TestCase):
    def test_from_string(self):
        card = Card.from_string("C1#3#1")

        self.assertEqual(card, Card(1, 3, 1))
        self.assertEqual(card.color, 1)
        self.assertEqual(card.value, 3)
        self.assertEqual(card.uniqueness_value, 1)

        # wrong color
        self.assertRaises(AssertionError, Card.from_string, "C9#3#1")

        # wrong value
        self.assertRaises(AssertionError, Card.from_string, "C2#6#1")

        # wrong uniqueness
        self.assertRaises(AssertionError, Card.from_string, "C1#1#3")

        self.assertRaises(AssertionError, Card.from_string, "C1#2#2")
        self.assertRaises(AssertionError, Card.from_string, "C1#3#2")
        self.assertRaises(AssertionError, Card.from_string, "C1#4#2")

        self.assertRaises(AssertionError, Card.from_string, "C1#5#1")

        # wrong format
        self.assertRaises(AssertionError, Card.from_string, "C1#5")
        self.assertRaises(AssertionError, Card.from_string, "x1#5#5")
        self.assertRaises(AssertionError, Card.from_string, "C1#5#-5")

    def test_string(self):
        card = Card.from_string("C1#3#1")

        self.assertEqual(str(card), "C1#3#1")

