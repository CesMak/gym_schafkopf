import unittest
from schafkopf import schafkopf
import numpy as np


opts_rnd   = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RANDOM", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "10", 8: "A"}}

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
        # worked: 24.08.2020
        test_game = self.initGame(opts_rnd, seed=22)
        assert test_game.active_player == 0

        # has card
        assert test_game.hasSpecificCard("A", "E", [test_game.players[0].hand], doConversion=True) == True
        assert test_game.hasSpecificCard("A", "S", [test_game.players[0].hand], doConversion=True) == False
        assert test_game.hasSpecificCard("U", "H", [test_game.players[0].hand], doConversion=True) == True

        test_str = ""
        for play in test_game.players:
            decl = test_game.getRufDeclarations([play.hand])
            test_str += decl[0]
            #print(decl)
        assert "ruf_Gruf_Eruf_Eruf_S" == test_str

        for play in test_game.players:
            print(test_game.getPossDeclarations([play.hand]))

        # phase 1 get highest declaration
        test_game.randomInitDeclarations()
        print("\n", test_game.declarations)
        print(test_game.getHighestDeclaration(test_game.declarations))

        print("\n\n")
        test_game.setDeclaration(test_game.declarations)
        print(test_game.matching)


if __name__ == '__main__':
    unittest.main()
