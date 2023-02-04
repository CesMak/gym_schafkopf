import gym   # use gym version0.23.1 pip install -U gym==0.23.1!!!
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
    # state = card_state(128) + add_states(18)+matching(4)+decl_options
    # card_state = [on_table, on_hand, played, play_options]
    state_dim  = env.observation_space.n #161
    # play_options(31) + decl_options(11)
    action_dim = env.action_space.n      #42

    print("Model state  dimension:", state_dim, "\nModel action dimension:", action_dim,"\n")

    env.printON = True

    # Play the declarations phase (everybody says weg)
    for card_idx in [32, 32, 32, 32]:
        state, rewards, done, info = env.step(card_idx)
