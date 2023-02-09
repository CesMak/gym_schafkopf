import random
import gym
import gym_schafkopf
from mcts.node import Node
from copy import deepcopy

opts_RL    = {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RL", "RL", "RL"], "nu_cards": 8, "active_player": 3, "seed": None, "colors": ['E', 'G', 'H', 'S'], "value_conversion": {1: "7", 2: "8", 3: "9", 4: "U", 5: "O", 6: "K", 7: "X", 8: "A"}}

class MonteCarloTree:
  '''
  Inspired by https://github.com/Taschee/schafkopf/blob/master/schafkopf/players/uct_player.py
  '''
  def __init__(self, game_state, player_hands, allowed_actions, ucb_const=1):
    self.root = Node(None, None, game_state, player_hands, allowed_actions)
    self.ucb_const = ucb_const
    self.treeList = []
    self.treeFilled = False

  def uct_search(self, num_playouts):
    for _ in range(num_playouts):
      selected_node = self.selection()
      rewards = self.simulation(selected_node)
      self.backup_rewards(leaf_node=selected_node, rewards=rewards)

    results = []
    for child in self.root.children:
      results.append((child.previous_action, child.visits, child.get_average_reward(self.root.game_state["cp"])))
    
    print(self.getTree(node=self.root), "\n-->Depth: ", self.getMaxDepth(), " Elements: ", len(self.treeList))
    self.printTree()
    return self.root.best_child(ucb_const=1).previous_action

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

    schafkopf_env           = gym.make("Schafkopf-v1", options_test=opts_RL)
    schafkopf_env.setGameState(deepcopy(node.game_state), deepcopy(node.player_hands))
    schafkopf_env.stepTest(chosen_action) # state, rewards, terminal, info

    new_node = Node(parent=node, game_state=deepcopy(schafkopf_env.getGameState()), previous_action=chosen_action, player_hands=deepcopy(schafkopf_env.getCards()), allowed_actions=schafkopf_env.test_game.getOptionsList())
    node.add_child(child_node=new_node)
    return new_node

  def simulation(self, selected_node):
    schafkopf_env           = gym.make("Schafkopf-v1", options_test=opts_RL)
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


  ## below only printing Tree functions:
  def getSimpleDepth(self, node, d=0):
    '''get simple depth at first children always'''
    if len(node.children)>0:
      return self.getDepth(node.children[0], d=d+1)
    else:
      return d

  def getMaxDepth(self):
    '''use getTree for that 
       this is quite easy cause treeList is a list that is already sorted by depth
    '''
    if not self.treeFilled:
      self.getTree(self.root)
    return self.treeList[len(self.treeList)-1][0]

  def subfinder(self, mylist, pattern):
      return list(filter(lambda x: x in pattern, mylist))

  def getTree(self, node, d=0):
    '''getTree(self.root) returns e.g. 
    self.treeList = [[0, 0, 37, -1], [0, 1, 34, -1], [0, 2, 39, -1], [0, 3, 36, -1], [0, 4, 32, -1], [0, 5, 41, -1], [1, 0, 40, 36], [1, 0, 40, 39], [1, 1, 32, 36], [1, 1, 32, 39], [1, 2, 38, 36], [1, 2, 38, 39], [1, 3, 33, 36], [1, 3, 33, 39], [1, 4, 39, 39], [1, 5, 34, 39], [2, 0, 37, 32], [2, 0, 41, 40], [2, 1, 35, 32], [2, 1, 36, 40]]
    with:
      [0,       0,           37,      -1],
       depth,   childnumber  action   parent that action belongs to (-1 means root)
    '''
    self.treeFilled = False
    if len(node.children)>0:
      for i,child in enumerate(node.children):
        if child.parent.previous_action is None:
            p = -1
        else:
            p = child.parent.previous_action
        a = [d, i, child.previous_action, p ]
        if len(self.subfinder(self.treeList, [a])) == 0:
          self.treeList.append(a)
          return self.getTree(child, d=d+1)
      if d>0:
        return self.getTree(node.parent, d=d-1)
      else:
        self.treeList.sort()
        self.treeFilled = True
        return self.treeList
    else:
      return self.getTree(node.parent, d=d-1)

  def printTree(self):
    '''[0, 0, 37, -1]
        d  c  a    p     depth child action parent
    '''
    res = []
    md = self.getMaxDepth()
    depth = 0
    depth_actions  = []
    for i in range(md+1):
                            # layers zwischenPlatz   #namen
      one_line = list("---"+md*(3*(2**md*"...."))+"---")      
      one_line[0]=str(i)
      one_line[len(one_line)-1]=str(i)
      one_line.append("\n")
      res.append(''.join(one_line))

    for i in self.treeList:
      [d, c, a, p]=i
      if d>depth:
        depth +=1
        depth_actions = []
      else:
        depth_actions.append(a)

      abstand=(md-d)*3
      ol = list(res[d])
      ol[3+abstand+c*(abstand+3)]=str(a)
      res[d]=''.join(ol)
      # else:
      #   # TODO bringe in reihenfolge von parents
      #   j = depth_actions.index(p)
      #   one_line[]
      #   res+=str(a)+".."
    for line in res: print(line)