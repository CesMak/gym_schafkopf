import gym
import gym_schafkopf

#used for batches and memory:
import random
from copy import deepcopy # used for baches and memory
import numpy as np
import datetime

# use ray for remote / parallel playing games speed up of 40%
import ray                                  # pip install ray==0.8.1   this does not work: pip install ray[rllib]
ray.init()                                  # num_cpus=12

# use for PPO Training:
import torch                                # pip3 install torch
import torch.nn as nn
from torch.distributions import Categorical
import torch.onnx                           # required for export as onnx
import onnx                                 # pip install onnx
import onnxruntime                          # pip install onnxruntime

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

@ray.remote
def playSteps(env, policy, steps, max_corr):
    batches = [Batch(), Batch(), Batch(), Batch()]
    result_memory = Memory()
    done   = 0
    state  = env.reset()
    for i in range(steps):
        player =  env.my_game.active_player
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

###
### in order to test the performance with random enemys:
###
@ray.remote
def playRandomSteps(policy, env, steps, max_corr):
    # difference here is that it is played until the END!
    finished_ai_reward  = 0
    finished_games      = 0
    total_ai_reward     = 0
    total_correct       = 0
    finished_random     = 0
    for i in range(steps):
        state  = env.resetRandomPlay_Env()
        done   = 0
        tmp    = 0
        corr_moves = 0
        while not done:
            action = policy.act(state, None)
            state, rewards, corr_moves, done = env.stepRandomPlay_Env(action, print__=False)
            if rewards is not None:
                tmp+=rewards[0]
            else:
                rewards = [-100, -100]
        if done and corr_moves == max_corr:
            finished_ai_reward +=rewards[0]
            finished_random    +=rewards[1]
            finished_games     +=1
        total_correct    +=corr_moves
        total_ai_reward  +=rewards[0]
    return finished_ai_reward, finished_games, total_ai_reward, total_correct, finished_random

def test_with_random(policy, env, jjj, max_corr, episodes=5000, print_game=5):
    finished_ai_reward, finished_games, total_ai_reward, total_correct, finished_random = 0.0, 0.0, 0.0, 0.0, 0.0
    nu_remote            = 10
    steps                = int(episodes/nu_remote)

    result = ray.get([playRandomSteps.remote(policy, env, steps, max_corr) for i in range(nu_remote)])
    for i in result:
        finished_ai_reward += i[0]
        finished_games     += i[1]
        total_ai_reward    += i[2]
        total_correct      += i[3]
        finished_random    += i[4]

    #print every nth game:
    if jjj%print_game == 0:
        state           = env.resetRandomPlay_Env(print__=True)
        done            = 0
        while not done:
            action = policy.act(state, None)
            state, ai_reward, corr_moves, done = env.stepRandomPlay_Env(action, print__=True)
        if done:
            print("Final ai reward:", ai_reward, "moves", corr_moves, "done", done)

    finished_games = int(finished_games)
    if finished_games>0:
        finished_ai_reward = finished_ai_reward/finished_games
        finished_random    = finished_random/finished_games
    total_ai_reward    = total_ai_reward/episodes
    total_correct      = total_correct/episodes

    return finished_games, finished_ai_reward, total_ai_reward, total_correct, finished_random

def learn_single(ppo, update_timestep, eps_decay, env, increase_batch, log_path, max_reward=-2.0):
    memory          = Memory()
    timestep        = 0
    log_interval    = 2           # print avg reward in the interval
    jjj             = 0
    wrong           = 0.0 # for logging
    nu_remote       = 10 #less is better, more games are finished! for update_timestep=30k 100 is better than 10 here!
    steps           = int(update_timestep/nu_remote)
    increase_batch  = int(increase_batch/nu_remote)
    i_episode       = 0
    max_corr_moves  = int(9)
    curr_batch_len  = 0
    print("","Batch size:", steps, "Increase Rate:", increase_batch, curr_batch_len, "\n\n")
    for uuu in range(0, 500000000+1):
        #### get Data in parallel:
        ttmp    = datetime.datetime.now()
        result = ray.get([playSteps.remote(env, ppo.policy_old, steps, max_corr_moves) for i in range(nu_remote)])
        for i in result:
            memory.append_memo(i)

        playing_time = round((datetime.datetime.now()-ttmp).total_seconds(),2)
        i_episode    += steps*nu_remote

        # update if its time
        if uuu % 1 == 0:
            #CAUTION MEMORY SIZE INCREASES SLOWLY HERE (during leraning correct moves...)
            # -> TODO use trainloader here! (random minibatch with fixed size)
            # TODO DO NOT SHUFFLE IN THIS WAY! Dann sind alle sequenzen durcheinander!
            memory.shuffle()
            bbb = memory.batch_from_Memory()
            curr_batch_len += len(bbb.actions)
            bbb.convert_batch_tensor()
            if curr_batch_len>0:
                ppo.my_update(bbb)
            del bbb
            memory.clear_memory()
            steps    += increase_batch

        # logging
        # if uuu % eps_decay == 0:
        #     print("currently do not use eps_decay....")
            #ppo.eps_clip *=0.8

        if uuu % log_interval == 0:
            jjj +=1
            finished_games, finished_ai_reward, total_ai_reward, total_correct, finished_random =  test_with_random(ppo.policy_old, env, jjj, max_corr_moves)
            #test play against random
            aaa = ('Game ,{:07d}, mean_rew of {} finished g. ,{:0.5}, of random ,{:0.5}, corr_moves[max:{:2}] ,{:4.4}, mean_rew ,{:1.3},   {},playing t={}, lr={}, batch={}\n'.format(i_episode, finished_games, float(finished_ai_reward), float(finished_random), int(max_corr_moves), float(total_correct), float(total_ai_reward), datetime.datetime.now()-start_time, playing_time, ppo.lr, curr_batch_len))
            print(aaa)
            curr_batch_len = 0

            #if total_ai_reward>max_reward and total_correct>2.0 and finished_games>10:
            if uuu % (log_interval*2) == 0:
                 path =  'PPO_noLSTM_{}_{}_{}_{}'.format(i_episode, finished_ai_reward, finished_games, total_ai_reward)
                 torch.save(ppo.policy.state_dict(), path+".pth")
                 max_reward = total_ai_reward
                 torch.onnx.export(ppo.policy_old.actor_critic, torch.rand(env.observation_space.n), path+".onnx")

            with open(log_path, "a") as myfile:
                myfile.write(aaa)

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
    increase_batch  = 100    # value is multipled with 10=nu_remote!! increase batch size every update step! (instead of lowering lr)
    train_from_start= True

    if train_from_start:
        print("train from start")
        eps = 0.1 # eps=0.2
        lr  = 0.01
        update_timestep = 30000
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
