# For exporting the model:
import torch.onnx
import onnx
import onnxruntime
import os
import gym
import gym_schafkopf
import numpy as np

def test_onnx(path, state, env):
    ort_session = onnxruntime.InferenceSession(path)
    ort_inputs  = {ort_session.get_inputs()[0].name: np.asarray(state, dtype=np.float32)}
    ort_outs    = ort_session.run(None, ort_inputs)
    actions, normalized_reward = ort_outs[0], ort_outs[1]

    # # unnormalize the reward??! --> aber was ist r.mean(), r.std() ?? immer anders?!
    # rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)
    std_reward  = 85  # assumed to be a constant from training
    mean_reward = -5.8  # assumed to be a constant from training
    unnormalized_reward = normalized_reward*(std_reward+1e-5)+mean_reward

    sorted_indices = np.argsort(actions)
    reversed_arr = sorted_indices[::-1]

    best_actions = reversed_arr[0:3]
    for i in best_actions:
        if i>=32:
            print("I would play now:", i, "-->", env.test_game.convertIndex2Decl(i), str(round(actions[i]*100, 2))+"%")
        else:
            print("I would play now:", i, "-->", env.test_game.idx2Card(i), str(round(actions[i]*100, 2))+"%")

    print("Normalized Reward:", normalized_reward.round(2), " Final Money: --> ", unnormalized_reward.round(2) )

    # max_value = (np.amax(actions))
    # result = np.where(actions == max_value)
    # return result[0][0], round(value[0], 3)


if __name__ == '__main__':
    train_path     = os.path.abspath(os.getcwd()) + "/PPO_noLSTM_40950000_23.237121667668873_4989_20.986.onnx"
    env = gym.make("Schafkopf-v1")
    state  = env.reset()
    env.test_game.printCurrentState()
    test_onnx(train_path, state, env)
