import random
import gym
import gym_schafkopf
from mcts.node import Node
from copy import deepcopy

class MonteCarloTree:
  '''
  Inspired by https://github.com/Taschee/schafkopf/blob/master/schafkopf/players/uct_player.py
  '''
  def __init__(self, game_state, player_hands, allowed_actions, ucb_const=1):
    self.root = Node(None, None, game_state, player_hands, allowed_actions)
    self.ucb_const = ucb_const

  def uct_search(self, num_playouts):
    for _ in range(num_playouts):
      selected_node = self.selection()
      rewards = self.simulation(selected_node)
      self.backup_rewards(leaf_node=selected_node, rewards=rewards)

    results = []
    for child in self.root.children:
      results.append((child.previous_action, child.visits, child.get_average_reward(self.root.game_state["cp"])))

    return results

  def selection(self):
    current_node = self.root
    while not current_node.is_terminal():
      if not current_node.fully_expanded():
        return self.expand(current_node)
      else:
        current_node = current_node.best_child(ucb_const=self.ucb_const)
    return current_node

  def expand(self, node):
    not_visited_actions = deepcopy(node.allowed_actions)
    for child in node.children:
      not_visited_actions.remove(child.previous_action)

    #TODO: check if this should be random or chosen by player policy
    chosen_action = random.choice(tuple(not_visited_actions))

    schafkopf_env           = gym.make("Schafkopf-v1")
    schafkopf_env.setGameState(deepcopy(node.game_state), deepcopy(node.player_hands))
    schafkopf_env.stepTest(chosen_action) # state, rewards, terminal, info

    new_node = Node(parent=node, game_state=deepcopy(schafkopf_env.getGameState()), previous_action=chosen_action, player_hands=deepcopy(schafkopf_env.getCards()), allowed_actions=schafkopf_env.test_game.getOptionsList())
    node.add_child(child_node=new_node)
    return new_node

  def simulation(self, selected_node):
    schafkopf_env           = gym.make("Schafkopf-v1")
    gameOver= deepcopy(selected_node.game_state)["gameOver"]
    schafkopf_env.setGameState(deepcopy(selected_node.game_state), deepcopy(selected_node.player_hands))

    while not gameOver:
      rewards, round_finished, gameOver = schafkopf_env.test_game.playUntilEnd()
    return rewards["final_rewards"]

  def backup_rewards(self, leaf_node, rewards):
    current_node = leaf_node
    while current_node != self.root:
      current_node.update_rewards(rewards)
      current_node.update_visits()
      current_node = current_node.parent
    self.root.update_visits()

  def get_action_count_rewards(self):
    result = {}
    for child in self.root.children:
      if isinstance(child.previous_action, list):
        result[tuple(child.previous_action)] = (child.visits, child.cumulative_rewards)
      else:
        result[child.previous_action] = (child.visits, child.cumulative_rewards)
    return result
