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

    #@unittest.skip("demonstrating skipping")
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

        print("\n\n Test get Options:")
        print(test_game.on_table_cards)
        opts  = test_game.getOptions(test_game.getInColor(test_game.on_table_cards), 0, orderOptions=False)
        cards = test_game.getValidOptions(test_game.on_table_cards, 0)
        print(cards)

        print("\n\n Test playing random")
        rewards, round_finished, gameOver =  test_game.playUntilAI(print_=True)
        print("Rewards:")
        print(rewards)

    #@unittest.skip("demonstrating skipping")
    def test_laufende(self):
        test_game = self.initGame(opts_rnd, seed=25)
        assert test_game.active_player == 0
        test_str = ""
        for play in test_game.players:
            decl = test_game.getRufDeclarations([play.hand])
            test_str += decl[0]
        test_game.randomInitDeclarations()
        print("\n", test_game.declarations)
        print(test_game.getHighestDeclaration(test_game.declarations))
        test_game.setDeclaration(test_game.declarations)
        print(test_game.matching)
        assert test_game.hasSpecificCard("O", "H", [test_game.players[1].hand], doConversion=True) == True
        assert test_game.hasSpecificCard("O", "E", [test_game.players[3].hand], doConversion=True) == True
        assert test_game.hasSpecificCard("O", "G", [test_game.players[3].hand], doConversion=True) == True
        assert test_game.matching["nuLaufende"] == 3

        print("\n\n Test get Options:")
        print(test_game.on_table_cards)
        opts  = test_game.getOptions(test_game.getInColor(test_game.on_table_cards), 0, orderOptions=False)
        cards = test_game.getValidOptions(test_game.on_table_cards, 0)
        print(cards)

        print("\n\n Test playing random")
        rewards, round_finished, gameOver =  test_game.playUntilAI(print_=True)
        assert rewards["final_rewards"][0] == -25

    #@unittest.skip("demonstrating skipping")
    def test_trumpFree(self):
        test_game = self.initGame(opts_rnd, seed=67)
        assert len(test_game.getTrumps([test_game.players[1].hand])) == 0

        for play in test_game.players:
            decl = test_game.getRufDeclarations([play.hand])
        test_game.randomInitDeclarations()
        print("\n", test_game.declarations)
        print(test_game.getHighestDeclaration(test_game.declarations))
        test_game.setDeclaration(test_game.declarations)
        print(test_game.matching)

        print("\n\n Test playing")
        for i in [1,1,3,1, 6,0,6,1, 0,0,5,3, 3,0,4,2, 1,0,0,3]:
            current_player = test_game.active_player
            card = test_game.players[current_player].hand[i]
            test_game.getRandomValidOption() # this is relevant!!!!!!!!! otherwise trumpFree and colorFree is not validated!
            print(test_game.current_round, test_game.player_names[current_player], test_game.player_types[current_player], card, len(test_game.players[current_player].hand), test_game.players[current_player].colorFree, test_game.players[current_player].trumpFree)
            rewards, round_finished, gameOver = test_game.step(i, True)

        print("Final Trump state:")
        for i in range(4):
            play = test_game.players[i]
            print(i, test_game.player_names[i],"trump cards:", test_game.getTrumps([play.hand]), "trump_free:", play.trumpFree)

        # Max and lea must be trump free now!
        assert len(test_game.getTrumps([test_game.players[1].hand])) ==0
        assert len(test_game.getTrumps([test_game.players[2].hand])) ==0

        assert int(test_game.players[0].trumpFree) == 1
        assert int(test_game.players[1].trumpFree) == 1

        # Jo and Tim, have no trumps but are not trumpFree
        assert len(test_game.getTrumps([test_game.players[2].hand])) ==0
        assert len(test_game.getTrumps([test_game.players[3].hand])) ==0
        assert int(test_game.players[2].trumpFree) == 0
        assert int(test_game.players[3].trumpFree) == 0

    #@unittest.skip("demonstrating skipping")
    def test_rufOptions(self):
        test_game = self.initGame(opts_rnd, seed=67)
        assert len(test_game.getTrumps([test_game.players[1].hand])) == 0

        for play in test_game.players:
            decl = test_game.getRufDeclarations([play.hand])
        test_game.randomInitDeclarations()
        print("\n", test_game.declarations)
        print(test_game.getHighestDeclaration(test_game.declarations))
        test_game.setDeclaration(test_game.declarations)
        print(test_game.matching)

        print("\n\n Test playing")
        for i in [2,3,2,6]:
            current_player = test_game.active_player
            card = test_game.players[current_player].hand[i]
            test_game.getRandomValidOption() # this is relevant!!!!!!!!! otherwise trumpFree and colorFree is not validated!
            print(test_game.current_round, test_game.player_names[current_player], test_game.player_types[current_player], card, len(test_game.players[current_player].hand), test_game.players[current_player].colorFree, test_game.players[current_player].trumpFree)
            rewards, round_finished, gameOver = test_game.step(i, True)
            # for i in test_game.players:
            #     print(i.trumpFree)

        # gerufen wird die Eichel Ass hier Jo darf hier als partner (2) die Eichel 9 jedoch nicht herausspielen!
        # da er die Ruf Ass hat.
        cards = test_game.getValidOptions(test_game.on_table_cards, test_game.active_player)
        print(cards)
        assert len(cards) == 6

    #@unittest.skip("demonstrating skipping")
    def test_winner(self):
        test_game = self.initGame(opts_rnd, seed=67)
        assert len(test_game.getTrumps([test_game.players[1].hand])) == 0

        for play in test_game.players:
            decl = test_game.getRufDeclarations([play.hand])
        test_game.randomInitDeclarations()
        print("\n", test_game.declarations)
        print(test_game.getHighestDeclaration(test_game.declarations))
        test_game.setDeclaration(test_game.declarations)
        print(test_game.matching)

        print("\n\n Test playing")
        for i in [2,3,2,6, 1,0,0,0, 2,2,1,0, 4,3,2,0, 0]:
            current_player = test_game.active_player
            card = test_game.players[current_player].hand[i]
            test_game.getRandomValidOption() # this is relevant!!!!!!!!! otherwise trumpFree and colorFree is not validated!
            print(test_game.current_round, test_game.player_names[current_player], test_game.player_types[current_player], card, len(test_game.players[current_player].hand), test_game.players[current_player].colorFree, test_game.players[current_player].trumpFree)
            rewards, round_finished, gameOver = test_game.step(i, True)

        # Max muesste hier nun auch Schelle frei sein!
        print(test_game.active_player)
        assert (test_game.active_player == 0)

    def test_colorFree(self):
        test_game = self.initGame(opts_rnd, seed=67)
        assert len(test_game.getTrumps([test_game.players[1].hand])) == 0

        for play in test_game.players:
            decl = test_game.getRufDeclarations([play.hand])
        test_game.randomInitDeclarations()
        print("\n", test_game.declarations)
        print(test_game.getHighestDeclaration(test_game.declarations))
        test_game.setDeclaration(test_game.declarations)
        print(test_game.matching)

        print("\n\n Test playing")
        for i in [2,3,2,6, 1,0,0,0, 2,2,1,0, 4,3,2,0, 0,0,0,0, 0,0,0,0]:
            current_player = test_game.active_player
            card = test_game.players[current_player].hand[i]
            test_game.getRandomValidOption() # this is relevant!!!!!!!!! otherwise trumpFree and colorFree is not validated!
            print(test_game.current_round, test_game.player_names[current_player], test_game.player_types[current_player], card, len(test_game.players[current_player].hand), test_game.players[current_player].colorFree, test_game.players[current_player].trumpFree)
            rewards, round_finished, gameOver = test_game.step(i, True)

        # Max muesste eichel frei sein
        # lea gruen und trumpf
        # jo greun und schelle
        # tim gruen

        assert test_game.players[0].colorFree[0] == 1.0
        assert test_game.players[1].colorFree[1] == 1.0
        assert test_game.players[1].trumpFree    == 1.0
        assert test_game.players[2].colorFree[1] == 1.0
        assert test_game.players[2].colorFree[3] == 1.0
        assert test_game.players[3].colorFree[1] == 1.0


if __name__ == '__main__':
    unittest.main()
