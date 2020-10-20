import gym
import gym_schafkopf
import numpy as np
from   mcts.mct import MonteCarloTree
from collections import OrderedDict

def run_mcts_minimal(env):
    cummulative_action_count_rewards = {}
    nu_samples  = 5
    nu_playouts = 20

    allowed_actions = env.test_game.getOptionsList()
    if len(allowed_actions) == 1:
        return allowed_actions[0]

    state           = env.test_game.getState().flatten().astype(np.int)
    gameState       = env.test_game.getGameState()

    for i in range(nu_samples):
        sampled_enemys = env.test_game.subSample(state, do_eval=False, print_=False)
        mct =  MonteCarloTree(gameState, sampled_enemys, allowed_actions)
        mct.uct_search(nu_playouts)
        action_count_rewards = mct.get_action_count_rewards()

        for action in action_count_rewards:
            if action in cummulative_action_count_rewards:
              cummulative_action_count_rewards[action] = (cummulative_action_count_rewards[action][0] + action_count_rewards[action][0], [cummulative_action_count_rewards[action][1][i] + action_count_rewards[action][1][i] for i in range(4)])
            else:
              cummulative_action_count_rewards[action] = action_count_rewards[action]

    best_action = max(cummulative_action_count_rewards.items(), key=lambda x : x[1][0])[0] # nimm action mit am meisten visits

    if isinstance(best_action, tuple):
      best_action = list(best_action)

    return best_action

def run_mcts(env):
    cummulative_action_count_rewards = {}
    nu_samples  = 5
    nu_playouts = 20

    state           = env.test_game.getState().flatten().astype(np.int)
    gameState       = env.test_game.getGameState()
    allowed_actions = env.test_game.getOptionsList()
    cp              = gameState["cp"]

    for i in range(nu_samples):
        sampled_enemys = env.test_game.subSample(state, do_eval=False, print_=False)
        mct =  MonteCarloTree(gameState, sampled_enemys, allowed_actions)
        mct.uct_search(nu_playouts)
        action_count_rewards = mct.get_action_count_rewards()

        for action in action_count_rewards:
            if action in cummulative_action_count_rewards:
              cummulative_action_count_rewards[action] = (cummulative_action_count_rewards[action][0] + action_count_rewards[action][0], [cummulative_action_count_rewards[action][1][i] + action_count_rewards[action][1][i] for i in range(4)])
            else:
              cummulative_action_count_rewards[action] = action_count_rewards[action]

    #od = OrderedDict(sorted(cummulative_action_count_rewards.items()))
    best_action = max(cummulative_action_count_rewards.items(), key=lambda x : x[1][0])[0] # nimm action mit am meisten visits
    #visits     = cummulative_action_count_rewards[best_action][0]
    # for key, value in od.items():
    #     print(key, value)
    # print("\n", best_action, "cpp:", cp)
    if isinstance(best_action, tuple):
      best_action = list(best_action)
    # tmp        = [x[0] for x in cummulative_action_count_rewards.values()] # list of all visits should be always = 100 nu_samples*nu_playouts
    # money      = cummulative_action_count_rewards[best_action][1][cp]
    # if best_action>=32:
    #     print(allowed_actions, env.test_game.convertIndex2DeclFixed(best_action), visits, visits / sum(tmp), round(money/visits,2))
    # else:
    #     print(allowed_actions, best_action, visits,  visits / sum(tmp), round(money/visits, 2) )
    return best_action#, visits / sum(tmp), round(money/visits,2)

def play_andTest():
    env_name = "Schafkopf-v1"
    env      = gym.make(env_name)

    state  = env.resetRandomPlay_Env(playStep=False)
    env.test_game.printCurrentState()
    print("\n")
    for i in range(8):
        best_action, av_visits, av_money = run_mcts(env)
        env.stepRandomPlay_Env(best_action, True)

def test_diffrentStartPlayer():
    env_name = "Schafkopf-v1"
    env      = gym.make(env_name, options_test={"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RANDOM", "RL", "RANDOM", "RANDOM"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}})
    env.resetRandomPlay_Env(print__=True)
    env.test_game.printCurrentState()
    print("\n")
    for i in range(2):
        best_action, av_visits, av_money = run_mcts(env)
        state, rewards, _, done = env.stepRandomPlay_Env(best_action, True) #state, [0, 0] False
        print(state, rewards, done)

def mcts_batch_test(env):
    env.test_game = env.my_game # use deepcopy here?!
    best_action, av_visits, av_money = run_mcts(env)
    state, rewards, _, done = env.stepRandomPlay_Env(best_action, True)
    return best_action, rewards, done

if __name__ == '__main__':
    #play_andTest()
    test_diffrentStartPlayer()
