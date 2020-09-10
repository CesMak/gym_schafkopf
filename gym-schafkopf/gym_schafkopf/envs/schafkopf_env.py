import gym
from   gym import spaces

from  .schafkopf import schafkopf # Point is important to use gameClasses from this folder!
import numpy as np

class SchafkopfEnv(gym.Env):
    def __init__(self, options = None):
        if options is None:
            options       = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RL", "RL", "RL"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "10", 8: "A"}}
        self.my_game  = schafkopf(options)
        self.correct_moves = 0

        ### Create the test game (only one RL)
        self.options_test   =  {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RANDOM", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "10", 8: "A"}}
        self.test_game      = schafkopf(self.options_test)

        states          = self.my_game.getState().flatten().astype(np.int).shape
        actions         = self.my_game.nu_players * self.my_game.nu_cards+len(self.my_game.decl_options)
        self.action_space      = gym.spaces.Discrete(actions)
        self.observation_space = gym.spaces.Discrete(states[0])

       # Reward style for train game:
        self.style = "final" # "final"
        self.printON = False

    def reset(self):
        'used in train game'
        self.my_game.reset()
        self.correct_moves = 0
        return self.my_game.getState().flatten().astype(np.int)

    def step(self, action):
        '''
        @action is the unique index of this card (e.g. from 0 to 31)
        @action if higher than 31:
            32          = weg
            33,34,35,36 = ruf_e, ruf_g, ruf_h, ruf_s
        @returns
        - state vector
        - reward according to style
        - done
        - info
        '''
        assert self.action_space.contains(action)
        rewards, round_finished, done = self.my_game.play_ai_move(action, print_=self.printON)
        rewardss, done = self.selectReward(rewards, round_finished, done, self.style)
        if done:
            if self.printON:
                print("\t Reward: ", rewardss, "Done:", done)
            state = self.reset()
        else:
            # following calls evaluateWinner!
            state = self.my_game.getState().flatten().astype(np.int)
        return state, rewardss, done, {"round_finished": round_finished, "correct_moves":  self.correct_moves}


    def selectReward(self, rewards, round_finished, done, style="final"):
        '''
        final:
            - returns -100 for wrong move
            - returns 0    for correct move
            - returns [x, x, x, x] at End of game (Rewards of 4 players)
        '''
        if style == "final":
            if rewards["ai_reward"] is None: # illegal move
                return -100, True #-100 before
            elif round_finished and done and rewards["state"] == "play" and not rewards["ai_reward"] is None:
                return rewards["final_rewards"], True
            else:
                self.correct_moves += 1
                return 0, False

    def stepRandomPlay_Env(self, ai_action, print__=False):
        'used for test game'
        print("hallo")

    def resetRandomPlay_Env(self, print__=False):
        'used for test game'
        print("hallo")
