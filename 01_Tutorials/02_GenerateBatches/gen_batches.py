import gym
import gym_schafkopf

#used for batches and memory:
import random
from copy import deepcopy # used for baches and memory
import numpy as np
import datetime

class Batch(object):
    def __init__(self):
        self.actions = []
        self.states = []
        self.logprobs = []
        self.rewards = []
        self.is_terminals = []

    def __unicode__(self):
        return self.show()
    def __str__(self):
        return self.show()
    def __repr__(self):
        return self.show()

    def show(self):
        return "[{}]__{}_{}".format( str(len(self.rewards)), ''.join(str(e) for e in self.rewards) , ''.join(str(e) for e in self.is_terminals))

    def clear_batch(self):
        #print("Clear memory:", len(self.actions), len(self.states), len(self.logprobs), len(self.rewards), len(self.is_terminals))
        del self.actions[:]
        del self.states[:]
        del self.logprobs[:]
        del self.rewards[:]
        del self.is_terminals[:]

    def append_batch(self, b):
        self.actions.extend(b.actions)
        self.states.extend(b.states)
        self.logprobs.extend(b.logprobs)
        self.rewards.extend(b.rewards)
        self.is_terminals.extend(b.is_terminals)

    # def convert_batch_tensor(self):
    #     self.states = torch.Tensor(self.states)
    #     self.actions= torch.Tensor(self.actions)
    #     self.logprobs = torch.Tensor(self.logprobs)
    #     #self.states = torch.from_numpy(self.states).float()
    #     #print(torch.from_numpy(self.states[0]).float())

class Memory:
    def __init__(self):
        self.batches = []

    def appendBatch(self, batch):
        #only append batch if it has data!
        if len(batch.actions)>0:
            self.batches.append(deepcopy(batch))

    def append_memo(self, input_memory):
        self.batches.extend(input_memory.batches)

    def shuffle(self):
        return random.shuffle(self.batches)

    def printMemory(self):
        print("Batches in the Memory:")
        for batch in self.batches:
            print(batch)
    def clear_memory(self):
        del self.batches[:]
    def batch_from_Memory(self):
        # converts to big batch
        b = Batch()
        for i in self.batches:
            b.append_batch(i)
        return b

def playSteps(env, steps, max_corr):
    batches       = [Batch(), Batch(), Batch(), Batch()]
    result_memory = Memory()
    done          = 0
    state         = env.reset()
    for i in range(steps):
        player =  env.my_game.active_player
        action = random.randrange(0, env.action_space.n)    # action hand index card comes in later tutorial from policy!

        if type(state) is np.ndarray:
            batches[player].states.append(state) # append old state = state before action
            batches[player].actions.append(int(action))
            batches[player].logprobs.append(float(0.2)) # value comes in later tutorial from policy!
        else:
            print("ERROR", state)

        state, rewards, done, _ = env.step(action)

        batches[player].is_terminals.append(done)

        if isinstance(rewards, int):
            batches[player].rewards.append(rewards)
        else:
            for jjj in range(4): # delete last element
                batches[jjj].rewards      = batches[jjj].rewards[:len(batches[jjj].is_terminals)-1] # for total of 4 players
                batches[jjj].is_terminals = batches[jjj].is_terminals[:len(batches[jjj].is_terminals)-1]
            for jjj in range(4): # append last element
                batches[jjj].rewards.append(float(rewards[jjj]))
                batches[jjj].is_terminals.append(True)
        if done:
            for jjj in range(4):
                result_memory.appendBatch(batches[jjj])
                batches[jjj].clear_batch()
        if done and (i+max_corr)>steps:
            break
    return result_memory

if __name__ == '__main__':
    ## Setup Env:
    env_name      = "Schafkopf-v1"

    # creating environment
    print("Creating model:", env_name)
    #env.reset()
    env = gym.make(env_name)
    #env.my_game.printHands()

    # Setup General Params
    state_dim  = env.observation_space.n
    action_dim = env.action_space.n

    print("Model state  dimension:", state_dim, "\nModel action dimension:", action_dim)

    env.printON = True

    # max_correct moves is necessary here to generate finished games!
    # otherwise batch size might vary more
    max_corr_moves  = int(env.action_space.n/4)

    print("Number of steps in one game:", max_corr_moves, "\n")
    # functions breaks if done(=invalid move or game finished)
    memory = playSteps(env, 10, max_corr_moves)
    batch  = memory.batches[0]

    print("\nOne Batch:")
    print("Actions:", batch.actions)
    print("State  :", batch.states)
    print("Rewards:", batch.rewards)
    print("LogProb:", batch.logprobs)
    print("Done   :", batch.is_terminals)
    print("State:", len(batch.states[0]))
    print(env.my_game.printCurrentState(batch.states[0]))

    # print("[Len of batch]__Reward_IsTerminal")
    # print(batch)


    nu_steps    = 10
    print("\nBenchmark playing "+str(nu_steps)+" games")
    env.printON = False
    start_time  = datetime.datetime.now()
    memory      = playSteps(env, nu_steps, max_corr_moves)
    print("Took:", datetime.datetime.now()-start_time, "Number of batches: ", len(memory.batches))
