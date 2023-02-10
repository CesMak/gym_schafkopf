import unittest
import gym
import numpy as np
from   mcts.mct import MonteCarloTree
import random
import gym_schafkopf
import json
from datetime import datetime

opts_rnd   = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RANDOM", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}}
opts_RL    = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RL", "RL", "RL"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}}
opts_mcts  = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RANDOM", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}}
opts_mcts2 = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RL", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}}

class gameLogic(unittest.TestCase):
    def setUp(self):
        print ("\n\nIn method", self._testMethodName,"\n")

    def init(self, seed=None, options=opts_mcts):
        self.env      = gym.make("Schafkopf-v1", seed=seed, options_test=options)
        self.env.resetRandomPlay_Env(print__=False, playStep=False)

    def getMCTSAction(self, test_game, nu_samples=5, nu_playouts=50, auto_adapt=False, print_=False):
        # auto is much faster!
        # if you call this cp must be RL player! 
        if test_game.player_types[test_game.getGameState()["cp"]] != "RL":
            print("Causion your first player is no RL Player play until its his choice")
            test_game.playUntilAI()

        state           = test_game.getState().flatten().astype(int)     #
        allowed_actions = test_game.getOptionsList()                   #<- [0 1 0 1...] 161x1 current state
        gameState       = test_game.getGameState()                      #<- possible Actions = [32,33,..]
        cp              = gameState["cp"]                               #<- current Player = 0

        if len(allowed_actions)==1:
            return allowed_actions[0]
        
        if auto_adapt:
            nu_cards = len(gameState["players"][cp].hand)
            nu_samples  = max(1, nu_cards-3)
            nu_playouts = len(allowed_actions)*4

        if print_: print("Find out best action for player: ", cp)
        action_list     = {}
        for i in range(nu_samples):
            sampled_enemys = test_game.subSample(state, do_eval=False, print_=False)
            mct =  MonteCarloTree(gameState, sampled_enemys, allowed_actions)
            best_action= mct.uct_search(nu_playouts)                                     # searches best node by playing with random actions until the end
        # TODO https://github.com/Taschee/schafkopf/blob/96c5b9199d9260b4fdd74de8a6e54805b407407b/schafkopf/players/uct_player.py#L132
        # evaluate result with best move! 
        #     for ba in dict_result.keys():
        #         if ba in action_list:
        #             action_list[ba]+=dict_result[ba]
        #         else:
        #             action_list[ba]=dict_result[ba]
        # if print_: print(action_list)
        # best_action = max(action_list, key=action_list.get)
        if print_:
            if best_action>32:
                print("best_action:", best_action, "-->", test_game.convertIndex2Decl(best_action))
            else:
                print("best_action:", best_action, "-->", test_game.idx2Card(best_action))
        return best_action

    def getSeedForGame(self, ba=40):
        # use this to get the correct seed!
        for i in range(42, 9000):
            self.init(seed=i, options=opts_mcts)
            tg     = self.env.test_game
            #tg.printCurrentState()
            baa = self.getMCTSAction(tg, nu_samples=6, print_=False)
            print(i, "-->", baa)
            # if ba==baa:
            #     return i
    def timeTest(self, seed=42, auto=False, nu_samples=5, nu_playouts=20, print_=False):
        t1 = datetime.now()
        self.init(seed=seed, options=opts_mcts)
        tg     = self.env.test_game
        if print_: tg.printCurrentState()
        for i in range(9):
            ba = self.getMCTSAction(tg, nu_samples=nu_samples, nu_playouts=nu_playouts, auto_adapt=auto, print_=False)
            self.env.stepRandomPlay_Env(ba, print__=print_)
        time = (datetime.now()-t1).total_seconds()
        points = tg.countResult(tg.getGameState()["players"][0].offhand)
        if auto:
            print("\nAuto Option Time:", time, "points:", points)  
        else:
            print("NO Auto Option Time:",  time, "points:", points)  
        return time, points

    @unittest.skip("demonstrating skipping")
    def test_wenz(self):
        # TODO does not work yet! 
        self.init(seed=13)
        for i in range(1):
            self.getMCTSAction(self.env.test_game)
            # state, rewards, corr_moves, done = env.stepRandomPlay_Env(best_action, print__=True) # TODO does not play a step!!! <- analyse that!

    @unittest.skip("demonstrating skipping")
    def test_player2IsRL(self):
        self.init(seed=14, options=opts_mcts2)
        tg     = self.env.test_game
        for i in range(1):
            self.getMCTSAction(tg, nu_samples=10)

    @unittest.skip("demonstrating skipping")
    def test_playMultipleActions_SoloG(self):
        #self.getSeedForGame(ba=39)
        self.init(seed=42, options=opts_mcts)
        tg     = self.env.test_game
        tg.printCurrentState()
        for i in range(9):
            ba = self.getMCTSAction(tg, nu_samples=6, nu_playouts=50, print_=False)
            self.env.stepRandomPlay_Env(ba, print__=True)

    @unittest.skip("demonstrating skipping")
    def test_autoMCTSTIME(self):
        #247,248,253,218, 184,193,
        #248,253,218,184,193, 232, 181, 230
                            #weg rE  wenz gei sE  sH    SE
        interesting_seeds = [42]
        tN = pN = tA =pA =0
        for i in interesting_seeds:
            t,p = self.timeTest(seed=i, nu_samples=7, nu_playouts=50, print_=False)
            tN += t
            pN += p
            t,p = self.timeTest(seed=i, auto=True)
            tA += t
            pA += p
        print("total Time   AUTO:", tA, "vs", tN)  
        print("total Points AUTO:", pA, "vs", pN)

    def test_allGames(self):     
        interesting_seeds = [248]
        for i in interesting_seeds:
            self.init(seed=i, options=opts_mcts)
            tg     = self.env.test_game
            tg.printCurrentState()
            for i in range(9):
                ba = self.getMCTSAction(tg, nu_samples=1, nu_playouts=15, print_=False)
                self.env.stepRandomPlay_Env(ba, print__=True)
if __name__ == '__main__':
    unittest.main()

# Why error with these seeds?
#        #247,248,253,218, 184,193,

# Use auto option for nuPlayers, num_samples
    # allowed actions
    # max depth are relevant here!
    # make it time-based?!

# Test Wenz, geier
# what is first wenz or geier
# do you have to have a u / o for wenz / geier?