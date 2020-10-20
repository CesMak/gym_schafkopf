import gym
import gym_schafkopf

#used for batches and memory:
import random
from copy import deepcopy # used for baches and memory
import numpy as np
import datetime

# use for PPO Training:
import torch                                # pip3 install torch
import torch.nn as nn
from torch.distributions import Categorical
import torch.onnx                           # required for export as onnx
import onnx                                 # pip install onnx
import onnxruntime                          # pip install onnxruntime

# for mcts better moves:
from test_mcts import run_mcts_minimal
from copy import deepcopy

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
        return "[{}]__{}_{}".format( str(len(self.rewards)), ','.join(str(e) for e in self.rewards) , ','.join(str(e) for e in self.is_terminals))

    def showDetailedBatchElements(self, env):
        for i in range(len(self.actions)):
            print("\n"+str(i)+"\t"+str(self.rewards[i])+"\t"+str(self.is_terminals[i])+"\t I choose "+str(self.actions[i])+" for:")
            env.test_game.printCurrentState(state=self.states[i])

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

    def convert_batch_tensor(self):
        self.states = torch.Tensor(self.states)
        self.actions= torch.Tensor(self.actions)
        self.logprobs = torch.Tensor(self.logprobs)
        #self.states = torch.from_numpy(self.states).float()
        #print(torch.from_numpy(self.states[0]).float())

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

class ActorModel(nn.Module):
    def __init__(self, state_dim, action_dim, nu_cards, n_latent_var):
        super(ActorModel, self).__init__()
        self.a_dim    = action_dim
        self.nu_cards = nu_cards
        self.ac       = nn.Linear(state_dim, n_latent_var)
        self.ac_prelu = nn.PReLU()
        self.ac1      = nn.Linear(n_latent_var, n_latent_var)
        self.ac1_prelu= nn.PReLU()

        # Actor layers:
        self.a1      = nn.Linear(n_latent_var+self.nu_cards, action_dim)

        # Critic layers:
        self.c1      = nn.Linear(n_latent_var, n_latent_var)
        self.c1_prelu= nn.PReLU()
        self.c2      = nn.Linear(n_latent_var, 1)

    def forward(self, input):
        # For 4 players each 15 cards on hand:
        # input=on_table(60)+ on_hand(60)+ played(60)+ play_options(60)+ add_states(15)
        # add_states = color free (4)+ would win (1) = 5  for each player
        #input.shape  = 15*4*4=240+3*5 (add_states) = 255

        #Actor and Critic:
        ac = self.ac(input)
        ac = self.ac_prelu(ac)
        ac = self.ac1(ac)
        ac = self.ac1_prelu(ac)

        # Get Actor Result:
        if len(input.shape)==1:
            options = input[self.nu_cards*3:self.nu_cards*4]
            actor_out =torch.cat( [ac, options], 0)
        else:
            options = input[:, self.nu_cards*3:self.nu_cards*4]
            actor_out   = torch.cat( [ac, options], 1)
        actor_out = self.a1(actor_out)
        actor_out = actor_out.softmax(dim=-1)

        # Get Critic Result:
        critic = self.c1(ac)
        critic = self.c1_prelu(critic)
        critic = self.c2(critic)

        return actor_out, critic

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, nu_cards, n_latent_var):
        super(ActorCritic, self).__init__()
        self.a_dim   = action_dim
        self.nu_cards= nu_cards

        # actor critic
        self.actor_critic = ActorModel(state_dim, action_dim, nu_cards, n_latent_var)

    def act(self, state, memory):
        if type(state) is np.ndarray:
            state = torch.from_numpy(state).float()
        action_probs, _ = self.actor_critic(state)
        # here make a filter for only possible actions!
        #action_probs = action_probs *state[self.a_dim*3:self.a_dim*4]
        dist = Categorical(action_probs)
        action = dist.sample()# -> gets the lowest non 0 value?!

        if memory is not None:
            #necessary to convert all to numpy otherwise deepcopy not possible!
            memory.states.append(state.data.numpy())
            memory.actions.append(int(action.data.numpy()))
            memory.logprobs.append(float(dist.log_prob(action).data.numpy()))

        return action.item()

    def evaluate(self, state, action):
        action_probs, state_value = self.actor_critic(state)
        dist = Categorical(action_probs)

        action_logprobs = dist.log_prob(action)
        dist_entropy    = dist.entropy()
        return action_logprobs, torch.squeeze(state_value), dist_entropy

class PPO:
    def __init__(self, state_dim, action_dim, nu_cards, n_latent_var, lr, betas, gamma, K_epochs, eps_clip):
        self.lr = lr
        self.betas = betas
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs

        self.policy = ActorCritic(state_dim, action_dim, nu_cards, n_latent_var)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=lr, betas=betas, weight_decay=5e-5) # eps=1e-5
        self.policy_old = ActorCritic(state_dim, action_dim, nu_cards, n_latent_var)
        self.policy_old.load_state_dict(self.policy.state_dict())
        #Do not use torch.optim.lr_scheduler to decrease lr. Increase Batch size instead!!! (see paper)
        self.MseLoss = nn.MSELoss() # MSELossFlat # SmoothL1Loss

    def monteCarloRewards(self, memory):
        # Monte Carlo estimate of state rewards:
        # see: https://medium.com/@zsalloum/monte-carlo-in-reinforcement-learning-the-easy-way-564c53010511
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(memory.rewards), reversed(memory.is_terminals)):
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma * discounted_reward)
            rewards.append(discounted_reward)
        rewards.reverse()
        # Normalizing the rewards:
        rewards = torch.tensor(rewards)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)
        return rewards

    def calculate_total_loss(self, state_values, logprobs, old_logprobs, advantage, rewards, dist_entropy):
        # 1. Calculate how much the policy has changed                # Finding the ratio (pi_theta / pi_theta__old):
        ratios = torch.exp(logprobs - old_logprobs.detach())
        # 2. Calculate Actor loss as minimum of 2 functions
        surr1       = ratios * advantage
        surr2       = torch.clamp(ratios, 1-self.eps_clip, 1+self.eps_clip) * advantage
        actor_loss  = -torch.min(surr1, surr2)
        # 3. Critic loss
        crictic_discount = 0.5
        critic_loss =crictic_discount*self.MseLoss(state_values, rewards)
        # 4. Total Loss
        beta       = 0.005 # encourage to explore different policies
        total_loss = critic_loss+actor_loss- beta*dist_entropy
        return total_loss

    def my_update(self, memory):
        # My rewards: (learns the moves!)
        rewards = torch.tensor(memory.rewards)
        rewards = self.monteCarloRewards(memory)

        # convert list to tensor
        old_states   = memory.states.detach()
        old_actions  = memory.actions.detach()
        old_logprobs = memory.logprobs.detach()

        # Optimize policy for K epochs:
        for _ in range(self.K_epochs):
            # Evaluating old actions and values :
            logprobs, state_values, dist_entropy = self.policy.evaluate(old_states, old_actions)
            advantages = rewards - state_values.detach()

            #rewards    = rewards.float()
            #advantages = advantages.float()
            loss       =  self.calculate_total_loss(state_values, logprobs, old_logprobs, advantages, rewards, dist_entropy)

            # take gradient step
            self.optimizer.zero_grad()
            loss.mean().backward()
            self.optimizer.step()

        # Copy new weights into old policy:
        self.policy_old.load_state_dict(self.policy.state_dict())

def playSteps(env, policy, steps, max_corr):
    batches = [Batch(), Batch(), Batch(), Batch()]
    result_memory = Memory()
    done   = 0
    state  = env.reset()
    for i in range(steps):
        player   =  env.my_game.active_player
        mcts_env = deepcopy(env)
        env.test_game = env.my_game
        mcts_action = run_mcts_minimal(env)

        action = policy.act(state, batches[player])# <- state is appended to memory in act function
        state, rewards, done, _ = env.step(mcts_action)
        batches[player].is_terminals.append(done)

        #print(action, mcts_action, done, rewards)
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

# both wont work.... in this case unfinished sequences occur.
def playStepsBoth(env, policy, steps, max_corr):
    batches = [Batch(), Batch(), Batch(), Batch()]
    result_memory = Memory()
    done   = 0
    state  = env.reset()
    for i in range(steps):
        player   =  env.my_game.active_player
        mcts_env = deepcopy(env)

        action = policy.act(state, batches[player])# <- state is appended to memory in act function
        batches[player].states.append(state) ## append mcts state before!
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

        ## append also mcts better move too batch:
        mcts_env.test_game = mcts_env.my_game
        mcts_action = run_mcts_minimal(mcts_env)
        _, rewards_mcts, done_mcts, _ = mcts_env.step(mcts_action)
        batches[player].is_terminals.append(done_mcts)
        batches[player].actions.append(mcts_action)
        batches[player].logprobs.append(0.0) ##??
        if isinstance(rewards_mcts, int):
            batches[player].rewards.append(rewards_mcts)
        else:
            for jjj in range(4): # delete last element
                batches[jjj].rewards      = batches[jjj].rewards[:len(batches[jjj].is_terminals)-1] # for total of 4 players
                batches[jjj].is_terminals = batches[jjj].is_terminals[:len(batches[jjj].is_terminals)-1]
            for jjj in range(4): # append last element
                batches[jjj].rewards.append(float(rewards_mcts[jjj]))
                batches[jjj].is_terminals.append(True)


        if done:
            for jjj in range(4):
                result_memory.appendBatch(batches[jjj])
                batches[jjj].clear_batch()
        if done and (i+max_corr)>steps:
            break
    return result_memory

def generateMCTSBatches(env, batches, state):
    done_mcts = 0
    while not done_mcts:
        cp = env.my_game.active_player
        batches[cp].states.append(state)
        env.test_game = env.my_game
        mcts_action = run_mcts_minimal(env)
        state, rewards_mcts, done_mcts, _ = env.step(mcts_action)
        batches[cp].is_terminals.append(done_mcts)
        batches[cp].actions.append(mcts_action)
        batches[cp].logprobs.append(0.0) ##??
        if isinstance(rewards_mcts, int):
            batches[cp].rewards.append(rewards_mcts)
        else:
            for jjj in range(4): # delete last element
                batches[jjj].rewards      = batches[jjj].rewards[:len(batches[jjj].is_terminals)-1] # for total of 4 players
                batches[jjj].is_terminals = batches[jjj].is_terminals[:len(batches[jjj].is_terminals)-1]
            for jjj in range(4): # append last element
                batches[jjj].rewards.append(float(rewards_mcts[jjj]))
                batches[jjj].is_terminals.append(True)

        if done_mcts:
            return batches

def playStepsBothEnd(env, policy, steps, max_corr):
    batches      = [Batch(), Batch(), Batch(), Batch()]
    mcts_batches = [Batch(), Batch(), Batch(), Batch()]
    result_memory = Memory()
    done   = 0
    state  = env.reset()
    for i in range(steps):
        player   =  env.my_game.active_player
        mcts_batches = generateMCTSBatches(deepcopy(env), mcts_batches, deepcopy(state))
        for jjj in range(4):
            result_memory.appendBatch(mcts_batches[jjj])
            mcts_batches[jjj].clear_batch()

        action = policy.act(state, batches[player])# <- state is appended to memory in act function
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

def learn_single(ppo, update_timestep, eps_decay, env, increase_batch, log_path, max_reward=-2.0):
    steps           = 2 # the move of each player is evaluated!
    max_corr_moves  = int(9)
    result = playStepsBothEnd(env, ppo.policy_old, steps, max_corr_moves)
    print("\n")
    result.printMemory()

    # output should be something like:
    # Batches in the Memory:
    # [9]__0,0,0,0,0,0,0,0,10.0_False,False,False,False,False,False,False,False,True
    # [9]__0,0,0,0,0,0,0,0,10.0_False,False,False,False,False,False,False,False,True
    # [9]__0,0,0,0,0,0,0,0,10.0_False,False,False,False,False,False,False,False,True
    # [9]__0,0,0,0,0,0,0,0,-30.0_False,False,False,False,False,False,False,False,True
    # [1]__-100_True

    # for batch in result.batches:
    #     batch.showDetailedBatchElements(env)

if __name__ == '__main__':
    ## Setup Env:
    env_name      = "Schafkopf-v1"
    start_time = datetime.datetime.now()

    # creating environment
    print("Creating model:", env_name)
    env = gym.make(env_name)

    # Setup General Params
    state_dim  = env.observation_space.n
    action_dim = env.action_space.n
    nu_cards   = 32 # number of cards can be on hand, on table, options, in offhand

    print("Model state  dimension:", state_dim, "\n\t= 0-31 on_table, 32-63 on_hand, 64-95 played, 96-127 play_options,\n\t= 128-145 Addstates =[would_win, is free of trump, color(EGHZ) free] 6x3\n\t 146-150 matching 1x4, 151-160 decl_options 1x10, 161 self.active_player", "\nModel action dimension:", action_dim, "\n\t 42: 1-32 index of cards, weg, ruf_E, ruf_G, ruf_S, wenz, geier, solo_E, solo_G, solo_H, solo_S")

    train_path     = "/home/markus/Documents/06_Software_Projects/gym_schafkopf/01_Tutorials/05_ImprovePretrained/pretrained.pth"
    nu_latent       = 128
    gamma           = 0.99
    K               = 16     #5
    increase_batch  = 20    # value is multipled with 10=nu_remote!! increase batch size every update step! (instead of lowering lr), 100
    train_from_start= True

    if train_from_start:
        print("train from start")
        eps = 0.1 # eps=0.2
        lr  = 0.01
        update_timestep = 500 # 1000
        eps_decay       = int(8000000/update_timestep) # is not used!
        ppo = PPO(state_dim, action_dim, nu_cards, nu_latent, lr, (0.9, 0.999), gamma, K, eps)

    else:
        # setup learn further:
        eps = 0.05               #train further1: 0.05   train further2: 0.01 train further3:  0.001
        lr  = 0.001              #train further1: 0.001  train further2: 0.0009, train further3 0.0001
        update_timestep = 5000  # train further1: 80000  train further2: 180000  train further2: 300000
        eps_decay   = 8000000 # is currently not used!
        ppo = PPO(state_dim, action_dim, nu_latent, lr, (0.9, 0.999), gamma, K, eps)
        ppo.policy.load_state_dict(torch.load(train_path))
        ppo.policy.actor_critic.eval()

    log_path        = "logging"+str(K)+"_"+str(update_timestep)+"_"+str(increase_batch)+"_"+str(random.randrange(100))+".txt"
    print("Parameters for training:\n", "Latent Layers:", nu_latent, "\n", "Learing Rate:", lr, " betas ", (0.9, 0.999),"\n","Gamma: ", gamma,"\n", "Epochs to train: ", K ,"\n","Epsillon", eps, " decay: ", eps_decay)

    learn_single(ppo, update_timestep, eps_decay, env, increase_batch, log_path)
