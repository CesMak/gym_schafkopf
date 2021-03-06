import gym
import gym_schafkopf

if __name__ == '__main__':
    ## Setup Env:
    env_name      = "Schafkopf-v1"

    # creating environment
    print("Creating model:", env_name)
    env = gym.make(env_name)
    env.reset()
    env.my_game.printHands()
    print("")

    #Setup General Params
    state_dim  = env.observation_space.n
    action_dim = env.action_space.n

    print("Model state  dimension:", state_dim, "\nModel action dimension:", action_dim,"\n")

    env.printON = True

    for card_idx in [32, 32, 32, 32]:
         state, rewards, done, info = env.step(card_idx)
