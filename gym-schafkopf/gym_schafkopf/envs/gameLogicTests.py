import unittest
from schafkopf import schafkopf
import numpy as np
import random
import json

opts_rnd   = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RANDOM", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}}
opts_RL    = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RL", "RL", "RL"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}}

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

    @unittest.skip("demonstrating skipping")
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

    @unittest.skip("demonstrating skipping")
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
        assert test_game.matching["nuLaufende"] == 2

        print("\n\n Test get Options:")
        print(test_game.on_table_cards)
        opts  = test_game.getOptions(test_game.getInColor(test_game.on_table_cards), 0, orderOptions=False)
        cards = test_game.getValidOptions(test_game.on_table_cards, 0)
        print(cards)

        print("\n\n Test playing random")
        rewards, round_finished, gameOver =  test_game.playUntilAI(print_=True)
        assert rewards["final_rewards"][0] == 20

    @unittest.skip("demonstrating skipping")
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

    @unittest.skip("demonstrating skipping")
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
        assert len(cards) == 7

    @unittest.skip("demonstrating skipping")
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

    @unittest.skip("demonstrating skipping")
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

    @unittest.skip("demonstrating skipping")
    def test_gymEnvState(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", options={"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RANDOM", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": 67, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}})
        env.reset()

        env.my_game.printHands()
        print("")

        cards_ordered = []
        for j in range(32):
            cards_ordered.append(env.my_game.idx2Card(j))

        print("Cards sorted by index:")
        print(cards_ordered,"\n")

        # Test Valid Options:
        print("\nDeclarations")
        env.my_game.randomInitDeclarations()
        print(env.my_game.declarations)
        print(env.my_game.getHighestDeclaration(env.my_game.declarations))
        env.my_game.setDeclaration(env.my_game.declarations)
        print(env.my_game.matching)

        play_options = env.my_game.getBinaryOptions(env.my_game.active_player, env.my_game.nu_players, env.my_game.nu_cards)
        cards        = env.my_game.state2Cards(play_options)
        assert (len(cards) == 8)
        print("")
        print("Options Max:", cards)
        print("Vector list:", play_options)

        print("\nPlay some cards")
        for i in [2,3,2,6, 1,0,0,0, 2,2,1,0, 4,3,2,0, 0,0,0,0, 0,0]:
            current_player = env.my_game.active_player
            card = env.my_game.players[current_player].hand[i]
            env.my_game.getRandomValidOption() # this is relevant!!!!!!!!! otherwise trumpFree and colorFree is not validated!
            print(env.my_game.current_round, env.my_game.player_names[current_player], env.my_game.player_types[current_player], card, len(env.my_game.players[current_player].hand))
            rewards, round_finished, gameOver = env.my_game.step(i, True)

        # Test cards_state:
        print("\nTest played cards state")
        on_table, on_hand, played =  env.my_game.getmyState(env.my_game.active_player, env.my_game.nu_players, env.my_game.nu_cards)
        print("Table      :",  env.my_game.state2Cards(on_table))
        print("Vector list:", on_table)
        assert on_table[6] == 1

        print("Hand       :",  env.my_game.state2Cards(on_hand))
        print("Vector list:", on_hand)
        assert on_hand.count(1) == 3

        print("played       :",  env.my_game.state2Cards(played))
        print("Vector list:", played)
        print("NOTE: played cards are invisible cards cards currently on the table are not played cards!")
        assert played.count(1) ==20

        # Test additional infos:
        print("\nGet additional States")
        add_states = [] #(nu_players-1)*6 = 18x1  enemy_1: [would_win, eghz color free, trumpfree]
        for i in range(len(env.my_game.players)):
            if i!=env.my_game.active_player:
                add_states.extend(env.my_game.getAdditionalState(i))
        print(add_states, len(add_states))

        matching = env.my_game.getMatchingBinary(env.my_game.active_player)
        print(matching)  # type should be Herz solo!
        print(env.my_game.matching)

        print("\nNow print the whole state nicely:")
        env.my_game.printCurrentState()
        # Result should look like this:
        # K of G_13 0 0
        # K of G_13 0 0
        # K of G_13 0 0
        # 	 on_table [10 of E_6, K of G_13]
        # 	 on_hand [10 of H_22, A of H_23, U of S_27]
        # 	 played [7 of E_0, 8 of E_1, 9 of E_2, U of E_3, O of E_4, K of E_5, A of E_7, 7 of G_8, 8 of G_9, 9 of G_10, U of G_11, O of G_12, 10 of G_14, A of G_15, 7 of H_16, 9 of H_18, 7 of S_24, 8 of S_25, 10 of S_30, A of S_31]
        # 	 options [10 of H_22, A of H_23, U of S_27]
        # 	 partners: Jo_2(you) play with Lea
        # 	 Add_state for  Max
        # 	 	  would_win 1 is free of trump 0 color(EGHZ) free [1 0 0 0]
        # 	 Add_state for  Lea
        # 	 	  would_win 0 is free of trump 1 color(EGHZ) free [0 1 0 0]
        # 	 Add_state for  Tim
        # 	 	  would_win 0 is free of trump 0 color(EGHZ) free [0 1 0 0]

    @unittest.skip("demonstrating skipping")
    def test_gymEnvPlaying(self):
        # learning
        # only RL player train against each other!
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", options={"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RL", "RL", "RL"], "nu_cards": 8, "active_player": 3, "seed": 67, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}})
        env.reset()

        env.my_game.printHands()
        print("")

        env.my_game.printCurrentState()

        print("Start playing use env")
        print("Model state  dimension:", env.observation_space.n, "\nModel action dimension:", env.action_space.n)
        env.printON = True

        for card_idx in [32, 32, 32, 32, 14, 15, 10, 0]:
             state, rewards, done, info = env.step(card_idx)
        assert done == False
        assert env.my_game.correct_moves == 8

    @unittest.skip("demonstrating skipping")
    def test_printState(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", options={"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RL", "RL", "RL"], "nu_cards": 8, "active_player": 3, "seed": 67, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}})
        state = env.reset()
        print("len-state:", len(state))

        env.my_game.printHands()
        print("")

        env.my_game.printCurrentState(state)

    @unittest.skip("demonstrating skipping")
    def test_playUntilAI(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", seed=55)
        state = env.resetRandomPlay_Env(print__=True)
        # print("len-state:", len(state))
        # env.test_game.printCurrentState(state)

        #now Lea has to play:
        for i in [32, 17, 11, 12, 15, 31, 18, 26, 17]:
            env.stepRandomPlay_Env(i, True)

        # # play next game?!
        # state = env.resetRandomPlay_Env(print__=True)
        # for i in [32, 31, 11, 12, 15, 18, 26, 25, 17]:
        #     env.stepRandomPlay_Env(i, True)
        #
        # # assert total rewards after second game:
        # assert (env.test_game.total_rewards[1] == 25)

    @unittest.skip("demonstrating skipping")
    def test_ramsch(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", seed=96)
        state = env.resetRandomPlay_Env(print__=True)
        # print("len-state:", len(state))
        # env.test_game.printCurrentState(state)

        #now Lea has to play:
        for i in [32, 22, 8, 24, 13, 0, 5, 1, 2]:
            env.stepRandomPlay_Env(i, True)
        assert env.test_game.rewards[2] == -30

        for i in range(4):
            print(env.test_game.player_names[i], env.test_game.rewards[i])
            print(env.test_game.players[i].offhand)

        # play next game:
        state = env.resetRandomPlay_Env(print__=True)
        assert env.test_game.active_player == 1
        for i in [32, 22]:
            env.stepRandomPlay_Env(i, True)

    @unittest.skip("demonstrating skipping")
    def test_solo_g(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", seed=180)
        state = env.resetRandomPlay_Env(print__=True)

        #now Lea has to play:
        for i in [38, 16, 1, 27, 14, 25, 7, 4, 28]:
            env.stepRandomPlay_Env(i, True)
        print(env.test_game.matching)
        assert env.test_game.rewards[0] == -120

    @unittest.skip("demonstrating skipping")
    def test_solo_geier(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", seed=26)
        state = env.resetRandomPlay_Env(print__=True)

        for i in [36]:
            env.stepRandomPlay_Env(i, True)

        #now Lea has to play:
        for i in [28, 16, 25, 5, 15, 27, 7, 30]:
            env.stepRandomPlay_Env(i, True)
        print(env.test_game.matching)
        assert env.test_game.rewards[3] == -75

    @unittest.skip("demonstrating skipping")
    def test_rufSpiel_1(self):
        import gym
        import gym_schafkopf# ruf declarations hightest seeds [59, 75, 76, 96, 97, 120, 123, 150, 162, 170, 185]
        env = gym.make("Schafkopf-v1", seed=59)
        state = env.resetRandomPlay_Env(print__=True)

        for i in [32]:
            env.stepRandomPlay_Env(i, True)

        #now Lea has to play:
        for i in [18, 12, 15, 26, 23, 22, 19, 21]:
            env.stepRandomPlay_Env(i, True)
        print(env.test_game.matching)

        # 0 = Max, 1=Lea, 2=Jo, 3=Tim
        # Max ruft mit Schelle den Jo beide verlieren
        # [-5, 5, -5, 5]
        assert env.test_game.matching["money"] == -5

    @unittest.skip("demonstrating skipping")
    def test_rufSpiel_1(self):
        import gym
        import gym_schafkopf# ruf declarations hightest seeds [59, 75, 76, 96, 97, 120, 123, 150, 162, 170, 185]
        env = gym.make("Schafkopf-v1", seed=59)
        state = env.resetRandomPlay_Env(print__=True)

        for i in [32]:
            env.stepRandomPlay_Env(i, True)

        #now Lea has to play:
        for i in [18, 12, 15, 26, 23, 22, 19, 21]:
            env.stepRandomPlay_Env(i, True)
        print(env.test_game.matching)

        # 0 = Max, 1=Lea, 2=Jo, 3=Tim
        # Max ruft mit Schelle den Jo beide verlieren
        # [-5, 5, -5, 5]
        assert env.test_game.matching["money"] == -5

    @unittest.skip("demonstrating skipping")
    def test_rufSpiel_2(self):
        import gym
        import gym_schafkopf# ruf declarations hightest seeds [59, 75, 76, 96, 97, 120, 123, 150, 162, 170, 185]
        env = gym.make("Schafkopf-v1", seed=75)
        state = env.resetRandomPlay_Env(print__=True)

        for i in [32]:
            env.stepRandomPlay_Env(i, True)

        #now Lea has to play:
        for i in [21, 15, 3, 26, 2, 8, 11, 10]:
            env.stepRandomPlay_Env(i, True)
        print(env.test_game.matching)

        # 0 = Max, 1=Lea, 2=Jo, 3=Tim
        # Max ruft Lea
        # [-5, 5, -5, 5]

    #@unittest.skip("demonstrating skipping")
    def test_solo_geier_first(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", seed=26)
        state = env.resetRandomPlay_Env(print__=True)

        for i in [37]:
            env.stepRandomPlay_Env(i, True)

        #now Lea has to play:
        for i in [28, 16, 25, 5, 15, 27, 7, 30]:
            env.stepRandomPlay_Env(i, True)
        print(env.test_game.matching)
        assert env.test_game.rewards[3] == -90

    @unittest.skip("demonstrating skipping")
    def test_solo_wenz(self):
        import gym
        import gym_schafkopf
        env = gym.make("Schafkopf-v1", seed=58)
        state = env.resetRandomPlay_Env(print__=True)

        for i in [36]:
            env.stepRandomPlay_Env(i, True)

        #now Lea has to play:
        for i in [8, 24, 21, 11, 3, 9, 13, 31]:
            env.stepRandomPlay_Env(i, True)
        print(env.test_game.matching)
        assert env.test_game.rewards[1] == 30

    @unittest.skip("demonstrating skipping")
    def test_davon_spielen(self): # weglaufen
        # lea sollte 4 grüne haben mit dem ass
        import gym
        import gym_schafkopf
        # for seeeede in range(20,2000):
        #     env = gym.make("Schafkopf-v1", seed=seeeede)
        #     state = env.resetRandomPlay_Env(print__=False)
        #     allowed_decl = env.test_game.getBinaryDeclarations(env.test_game.active_player)
        #
        #     cards_lea   = env.test_game.players[1].hand
        #     green_cards = env.test_game.getColoredCards([cards_lea], "G")
        #     has_GA      = env.test_game.hasSpecificCard("A", "G", [green_cards], doConversion=True)
        #     if len(green_cards)>3 and has_GA:
        #         print(seeeede)
        #         break

        test_game = self.initGame(opts_RL, seed=68)
        test_game.declarations = ["weg", "weg", "weg", "ruf_G"]
        print(test_game.getHighestDeclaration(test_game.declarations))
        test_game.setDeclaration(test_game.declarations)
        print(test_game.matching, test_game.phase)

        for i in [26,11,24,25, 10, 28, 9, 16]:
            cp = test_game.active_player
            test_game.getRandomValidOption() # this is relevant!!!!!!!!! otherwise trumpFree and colorFree is not validated!
            # print(test_game.current_round, test_game.player_names[current_player], test_game.player_types[current_player], card, len(test_game.players[current_player].hand), test_game.players[current_player].colorFree, test_game.players[current_player].trumpFree)
            hand_idx = test_game.idx2Hand(i, cp)
            card = test_game.players[cp].hand[hand_idx]
            print(test_game.current_round, test_game.player_names[cp], test_game.player_types[cp], card, len(test_game.players[cp].hand), test_game.players[cp].colorFree, test_game.players[cp].trumpFree)
            rewards, round_finished, gameOver = test_game.step(test_game.idx2Hand(i, cp), print_=True)

    @unittest.skip("demonstrating skipping")
    def test_generate_quizz1(self):
        import gym
        import gym_schafkopf
        final_dict = {}
        for j in range(1000):
            test_game = self.initGame(opts_RL, seed=None)
            trumps       = ["solo_H", "solo_H", "solo_H", "solo_E", "solo_G", "solo_S"]
            trump        = trumps[random.randrange(len(trumps)-1)]
            test_game.declarations = ["weg", "weg", "weg", trump]
            test_game.setDeclaration(test_game.declarations)

            names        = ["James", "Alicia", "Lily", "Albus", "Poppy", "Antioch", "Ernie", "Bob", "Draco", "Mafalda", "Igor", "Viktor", "Alecto", "Fleur", "Ariana", "Petunia", "Cho", "Colin", "Dirk", "Barty", "Amelia", "Susan", "Frank", "Ludo", "Phineas", "Ginny", "Neville", "Nigellius", "Boot", "Bryce", "Bilius", "Jean", "Lucius", "Percival", "Rubius", "Molly", "Sirius", "Severus", "Luna"]
            dict_names   = []
            all_cards    = []
            random_cards = []
            for i in test_game.players:
                all_cards.extend(i.hand)
            for i in range(4):
                tmp = random.randrange(len(all_cards)-1)
                uuu = all_cards.pop(tmp)
                random_cards.append(uuu)

                tmp_names = random.randrange(len(names)-1)
                vvv = names.pop(tmp_names)
                dict_names.append(vvv)
            winning_card, on_table_win_idx, player_win_idx = test_game.evaluateWinner(random_cards)
            result = test_game.countResult([random_cards])

            # convert cards O of H_20 --> HO
            cards_ = []
            for i in random_cards:
                tmp = str(i).replace(" of ", "").split("_")[0]
                tmp = tmp[1]+tmp[0]
                cards_.append(tmp)
            final_dict[j] = {"cards": cards_, "names": dict_names, "winner_idx": on_table_win_idx, "points": result, "trump": test_game.matching["trump"]}
        with open('quizz_1.json', 'w') as fp:
            json.dump(final_dict, fp)
        #final_dict = {"1": {"cards": ["EA"], "owners": ["markus"], "winner_idx": 0, "points": 10}}

        # if print_: print("\t Winner:"+self.player_names[player_win_idx]+" with "+str(winning_card)+" sits on "+str(on_table_win_idx)+" at the table"  )
        # trick_rewards[player_win_idx] = self.countResult([self.on_table_cards])
                    # <div class="playingCards schafkopf input-group">
                    #   <form>  <fieldset>  <legend>markus</legend>   <span class="deck-1 card HK" title="Herz König"></span> </fieldset>  </form>
                    #   <form>  <fieldset>  <legend>markus</legend>   <span class="deck-1 card HK" title="Herz König"></span> </fieldset>  </form>
                    #   <form>  <fieldset>  <legend>markus</legend>   <span class="deck-1 card HK" title="Herz König"></span> </fieldset>  </form>
                    #   <form>  <fieldset>  <legend>markus</legend>   <span class="deck-1 card HK" title="Herz König"></span> </fieldset>  </form>
                    # </div>

if __name__ == '__main__':
    unittest.main()

        # for seeeede in range(20,2000):
        #     env = gym.make("Schafkopf-v1", seed=seeeede)
        #     state = env.resetRandomPlay_Env(print__=True)
        #     allowed_decl = env.test_game.getBinaryDeclarations(env.test_game.active_player)
        #     if allowed_decl[4] == 1.0:
        #         print(seeeede)
        #         for i in [36]:
        #             env.stepRandomPlay_Env(i, True)
        #         if "wenz" in env.test_game.matching["type"]:
        #             print("seeeeed:", seeeede)
        #             break
