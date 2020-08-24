import unittest
from schafkopf import schafkopf
import numpy as np

opts_rnd   = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RANDOM", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {11: "^11", 15: "J"}}

class gameLogic(unittest.TestCase):
    def setUp(self):
        print ("\n\nIn method", self._testMethodName,"\n")

    def initGame(self, opts, seed=None):
        opts["seed"] = seed
        test_game     = schafkopf(opts)
        test_game.reset()

        test_game.printHands()
        print("\n")
        return test_game

    def test_deck(self):
        test_game = self.initGame(opts_rnd, seed=22)

        #shift cards:
        # for i in [1, 3, 9, 0, 5, 12, 10, 2]:
        #     rewards, corr_move, done = test_game.play_ai_move(i, print_=True)
        #
        # print("\n")
        # tricks = [[47, 49, 48, 46],[53,54,57,58]]
        # for i in tricks:
        #     for j in i:
        #         rewards, corr_move, done = test_game.play_ai_move(j, print_=True)


if __name__ == '__main__':
    unittest.main()
