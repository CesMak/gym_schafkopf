# quick fix to work in gameLogicTests and for environment tests
try:
    from .gameClasses import game
except:
    from gameClasses import game

import numpy as np
import random

class schafkopf(game):
    def __init__(self, options_dict):
        super().__init__(options_dict)

        # Specific for Schafkopf:
        self.shifted_cards     = 0 # counts
        self.nu_shift_cards    = options_dict["nu_shift_cards"] # shift 2 cards!  # set to 0 to disable
        self.shifting_phase    = True
        self.shift_option      = 2 # due to gym reset=2 ["left", "right", "opposide"]
        self.correct_moves     = 0 # is not used or?!
        super().setup_game()       # is required here already for gym to work!

    def reset(self):
        self.nu_games_played +=1
        self.shifted_cards  = 0

        if self.shift_option <2:
            self.shift_option += 1
        else:
            self.shift_option  = 0
        if self.nu_shift_cards>0:
            self.shifting_phase    = True
        else:
            self.shifting_phase    = False
        self.players           = []  # stores players object
        self.on_table_cards    = []  # stores card on the table
        self.played_cards      = []  # of one game # see also in players offhand!
        self.gameOver          = 0
        self.rewards           = np.zeros((self.nu_players,))
        self.current_round     = 0
        super().setup_game()
        self.active_player     = self.nextGamePlayer()
        self.correct_moves     = 0


    def play_ai_move(self, ai_card_idx, print_=False):
        'card idx from 0....'
        current_player    =  self.active_player
        card_options__    = self.getValidOptions(current_player)# cards
        card              = self.idx2Card(ai_card_idx)
        player_has_card   = self.players[current_player].hasSpecificCardOnHand(ai_card_idx)
        tmp               = card.idx
        card_options      = self.cards2Idx(card_options__)
        if player_has_card and tmp in card_options and "RL" in self.player_types[current_player]:
            if print_:
                if self.shifting_phase and self.nu_shift_cards>0:
                    print("[{}] {} {}\t shifts {}\tCard {}\tCard Index {}\t len {}".format(self.current_round, current_player, self.player_names[current_player], self.player_types[current_player], card, ai_card_idx, len(self.players[current_player].hand)))
                else:
                    print("[{}] {} {}\t plays {}\tCard {}\tCard Index {}\t len {}  options {} on table".format(self.current_round, current_player, self.player_names[current_player], self.player_types[current_player], card, ai_card_idx, len(self.players[current_player].hand), card_options__), self.on_table_cards)
            self.correct_moves +=1
            rewards, round_finished, gameOver = self.step(self.idx2Hand(tmp, current_player), print_)
            if print_ and round_finished:
                print(rewards, self.correct_moves, gameOver, "\n")
            return rewards, round_finished, gameOver
        else:
            if print_:
                if not player_has_card:
                    print("Caution player does not have card:", card, " choose one of:", self.idxList2Cards(card_options))
                if not tmp in card_options:
                    print("Caution option idx", tmp, "not in (idx)", card_options)
                if not "RL" in self.player_types[current_player]:
                    print("Caution", self.player_types[current_player], self.active_player, "is not of type RL", self.player_types)
            return {"state": "play_or_shift", "ai_reward": None}, False, True # rewards round_finished, game_over

    def playUntilAI(self, print_=False):
        rewards        = {"state": "play_or_shift", "ai_reward": None}
        gameOver       = False
        round_finished = False
        while len(self.players[self.active_player].hand) > 0:
            current_player = self.active_player
            if "RANDOM" in self.player_types[current_player]:
                if  self.shifting_phase and self.nu_shift_cards>0:
                    hand_idx_action = self.getRandomCard()
                    card            = self.players[current_player].hand[hand_idx_action]
                    if print_:
                        print("[{}] {} {}\t shifts {}\tCard {}\tHand Index {}\t len {}".format(self.current_round, current_player, self.player_names[current_player], self.player_types[current_player], card, hand_idx_action, len(self.players[current_player].hand)))
                else:
                    card            = self.getRandomValidOption()
                    hand_idx_action = self.players[self.active_player].hand.index(card)
                    if print_:
                        print("[{}] {} {}\t plays {}\tCard {}\tHand Index {}\t len {}".format(self.current_round, current_player, self.player_names[current_player], self.player_types[current_player], card, hand_idx_action, len(self.players[current_player].hand)))
                rewards, round_finished, gameOver = self.step(hand_idx_action, print_)
                if print_ and round_finished:
                    print("")
            else:
                return rewards, round_finished, gameOver
        # Game is over!
        #CAUTION IF GAME OVER NO REWARDS ARE RETURNED
        #rewards = {'state': 'play_or_shift', 'ai_reward': None}
        return rewards, True, True



    def stepRandomPlay(self, action_ai, print_=False):
        # fängt denn ai überhaupt an???
        # teste ob correct_moves korrekt hochgezählt werden?!
        rewards, round_finished, gameOver = self.play_ai_move(action_ai, print_=print_)
        if rewards["ai_reward"] is None: # illegal move
            return None, self.correct_moves, True
        elif gameOver and "final_rewards" in rewards:
            # case that ai plays last card:
            mean_random = (sum(rewards["final_rewards"])- rewards["final_rewards"][1])/3
            return [rewards["final_rewards"][1], mean_random], self.correct_moves, gameOver
        else:
            #case that random player plays last card:
            if "RL" in self.player_types[self.active_player]:
                return [0, 0], self.correct_moves, gameOver
            else:
                rewards, round_finished, gameOver = self.playUntilAI(print_=print_)
                ai_reward   = 0
                mean_random = 0
                if gameOver and "final_rewards" in rewards:
                    mean_random = (sum(rewards["final_rewards"])- rewards["final_rewards"][1])/3
                    ai_reward = rewards["final_rewards"][1]
                return [ai_reward, mean_random], self.correct_moves, gameOver

    def getInColor(self):
        # returns the leading color of the on_table_cards
        # if only joker are played None is returned
        for i, card in enumerate(self.on_table_cards):
            if card is not None:
                if card.value <15:
                    return card.color
        return None

    def getRandomPossCards(self, list, nuCards):
        random.seed(None)
        result = []
        for i in range(nuCards):
            tmp = random.randrange(len(list))
            result.append(list[tmp])
            del list[tmp]
        return result

    def removeColor(self, my_list, color):
        my_list = self.idxList2Cards(my_list)
        for n, i in enumerate(my_list):
            if i.color == color:
                del my_list[n]
        return self.cards2Idx(my_list)

    def removeList(self, input, to_be_removed):
        # caution deletes from both lists
        return list(set(input)-set(to_be_removed))

    def similarityList(self, a, b):
        return len(set(a).intersection(b))

    def subSample(self, state, do_eval=True, print_=True):
        # get subSample Sets for enemy players
        # possible Cards a player could have
        #{3: [54, 57, 51], 2: [47, 50, 58], 0: [33, 4, 32], 'matches': 44.4}
        # returns the player index and the card index of subsampling as well as the percentage of correct matched cards

        ll    = self.nu_players * self.nu_cards
        on_table, on_hand, played, play_options, add_states = state[0:ll], state[ll:2*ll], state[ll*2:3*ll], state[3*ll:4*ll], state[4*ll:len(state)]
        test_deck_idx = self.cards2Idx(self.createDeck().cards)
        left_cards    = self.state2Cards(on_table+on_hand+played)
        rem_cards     = self.cards2Idx(left_cards)

        tmp_cards  = self.removeList(test_deck_idx, rem_cards)
        start_cards = len(tmp_cards)
        if print_: print(len(tmp_cards), tmp_cards, "-->", self.idxList2Cards(tmp_cards))

        ap     = self.active_player
        enemys = list(range(self.nu_players))
        enemys.remove(ap)

        # sort enemys by number of color free otherwise not enough cards are left
        enemys_free_score = [int(sum(self.players[x].colorFree)) for x in enemys]
        enemys_free_score.sort()
        enemys_sorted = [x for _,x in sorted(zip(enemys_free_score, enemys), reverse=True)]
        result  = {}
        matches = 0
        for i in enemys_sorted:
            enemy      = self.players[i]
            play_idxs = tmp_cards
            for n, m in enumerate(["B", "G", "R", "Y"]):
                if enemy.colorFree[n]>=1.0:
                    play_idxs = self.removeColor(play_idxs, m)
            cards = self.getRandomPossCards(play_idxs, len(enemy.hand))
            tmp_cards = self.removeList(tmp_cards, cards)
            result[i] = cards
            if do_eval:
                matches += self.similarityList(self.cards2Idx(enemy.hand), cards)
            if print_: print(enemy.name, enemy.hand, enemy.colorFree, self.idxList2Cards(cards))
        result["matches"] = round((matches/start_cards)*100, 1)
        return result

    def evaluateWinner(self):
        #uses on_table_cards to evaluate the winner of one round
        #returns winning card
        #player_win_idx: player that one this game! (0-3)
        #on_table_win_idx: player in sequence that one!
        highest_value    = 0
        winning_card     = self.on_table_cards[0]
        incolor          = self.getInColor()
        on_table_win_idx = 0
        if  incolor is not None:
            for i, card in enumerate(self.on_table_cards):
                # Note 15 is a Jocker
                if card is not None and ( card.value > highest_value and card.color == incolor and card.value<15):
                    highest_value = card.value
                    winning_card = card
                    on_table_win_idx = i
        player_win_idx = self.player_names.index(winning_card.player)
        return winning_card, on_table_win_idx, player_win_idx

    def getState(self):
        play_options = self.getBinaryOptions(self.active_player, self.nu_players, self.nu_cards)
        #play_options = self.convertAvailableActions(play_options)
        on_table, on_hand, played = self.getmyState(self.active_player, self.nu_players, self.nu_cards)
        add_states = [] #(nu_players-1)*5
        for i in range(len(self.players)):
            if i!=self.active_player:
                add_states.extend(self.getAdditionalState(i))
        return np.asarray([on_table+ on_hand+ played+ play_options+ add_states])

    def getValidOptions(self, player):
        # returns card of valid options
        if self.shifting_phase and self.nu_shift_cards>0:
            options = [x for x in range(len(self.players[player].hand))] # hand index
        else:
            options = self.getOptions(self.getInColor(), player) # hand index
        # return as cards
        return [self.players[player].hand[i] for i in options]

    def convertTakeHand(self, player, take_hand):
        converted_cards = []
        for card in take_hand:
            card.player = player.name
            converted_cards.append(card)
        return converted_cards

    def step(self, card_idx, print_=False):
        #Note that card_idx is a Hand Card IDX!
        # it is not card.idx unique number!
        self.shifting_phase = (self.shifted_cards<=self.nu_players*self.nu_shift_cards)
        if self.shifting_phase and self.nu_shift_cards>0:
            shift_round   = int(self.shifted_cards/self.nu_players)
            self.shiftCard(card_idx, self.active_player, self.getShiftPlayer())
            self.shifted_cards +=1

            round_finished = False
            if self.shifted_cards%self.nu_players == 0:
                round_finished = True
            #if print_: print("Shift Round:", shift_round, "Shifted Cards:", self.shifted_cards, "round_finished", round_finished)
            if shift_round == (self.nu_shift_cards)-1 and round_finished:
                if print_: print("\nShifting PHASE FINISHED!!!!!!\n")
                for player in self.players:
                    # convert cards of take hand card.player to correct player!
                    player.take_hand = self.convertTakeHand(player, player.take_hand)
                    player.hand.extend(player.take_hand)
                    if print_: print(player.name, "takes now", player.take_hand, " all cards", player.hand)
                self.shifted_cards  = 100
                self.shifting_phase = False
            self.active_player = self.getNextPlayer()
            return {"state": "shift", "ai_reward": 0}, round_finished, False # rewards, round_finished, gameOver
        else:
            # in case card_idx is a simple int value
            round_finished = False
            # play the card_idx:
            played_card = self.players[self.active_player].hand.pop(card_idx)
            self.on_table_cards.append(played_card)
            # Case round finished:
            trick_rewards    = [0]*self.nu_players
            on_table_win_idx = -1
            player_win_idx   = -1
            if len(self.on_table_cards) == self.nu_players:
                winning_card, on_table_win_idx, player_win_idx = self.evaluateWinner()
                trick_rewards[player_win_idx] = self.countResult([self.on_table_cards], self.players[player_win_idx].offhand)
                self.current_round +=1
                self.played_cards.extend(self.on_table_cards)
                self.players[player_win_idx].appendCards(self.on_table_cards)
                self.on_table_cards = []
                self.active_player  = player_win_idx
                round_finished = True

            else:
                self.active_player = self.getNextPlayer()

            if round_finished and len(self.played_cards) == self.nu_cards*self.nu_players:
                self.assignRewards()
            if self.isGameFinished():
                self.assignRewards()
                for i in range(len(self.total_rewards)):
                    self.total_rewards[i] +=self.rewards[i]
    		#yes this is the correct ai reward in case all players are ai players.
            return {"state": "play", "ai_reward": trick_rewards[player_win_idx], "on_table_win_idx": on_table_win_idx, "trick_rewards": trick_rewards, "player_win_idx": player_win_idx, "final_rewards": self.rewards}, round_finished, self.isGameFinished()

    def getAdditionalState(self, playeridx):
        # result = [would win, bgry color free]
        result = []
        player = self.players[playeridx]

        #extend if this player would win the current cards
        player_win_idx = playeridx
        if len(self.on_table_cards)>0:
            winning_card, on_table_win_idx, player_win_idx = self.evaluateWinner()
        if player_win_idx == playeridx:
            result.extend([1])
        else:
            result.extend([0])
        result.extend(player.colorFree) # 4 per player -> 12 states
        return result

    def getmyState(self, playeridx, players, cards):
        # should be 60 here in case of error!
        on_table, on_hand, played =[0]*players* cards, [0]*players* cards, [0]*players* cards
        for card in self.on_table_cards:
            on_table[card.idx]= 1

        for card in self.players[playeridx].hand:
            on_hand[card.idx] =1

        for card in self.played_cards:
            played[card.idx] = 1
        return on_table, on_hand, played

    def getOptions(self, incolor, player, orderOptions=False):
        # incolor = None -> Narr was played played before
        # incolor = None -> You can start!
        # Return Hand index

        cards        = self.players[player].hand

        options = []
        hasColor = False
        if incolor is None:
            for i, card in enumerate(cards):
                options.append(i)
        else:
            for i, card in enumerate(cards):
                if card.color == incolor and card.value <15:
                    options.append(i)
                    hasColor = True
                if card.value == 15: # append all joker
                    options.append(i)

        # if has not color and no joker append all cards!
        # wenn man also eine Farbe aus ist!
        if not hasColor:
            options = [] # necessary otherwise joker double!
            for i, card in enumerate(cards):
                options.append(i)
            if incolor is not None: # no do not check for joker here!
                self.players[player].setColorFree(incolor)
        if orderOptions: return sorted(options, key = lambda x: ( x[1].color,  x[1].value))
        return options


    def hasJoker(self, cards):
        for i in ["Y", "R", "G", "B"]:
            if super().hasSpecificCard(15, i, cards):
                return True
        return False

    def hasYellowEleven(self, cards):
        return self.hasSpecificCard(11, "Y", cards)

    def hasRedEleven(self, cards):
        return self.hasSpecificCard(11, "R", cards)

    def hasBlueEleven(self, cards):
        return self.hasSpecificCard(11, "B", cards)


    def countResult(self, input_cards, offhandCards):
        #input_cards = [[card1, card2, card3, card4], [stich2], ...]
        # in class player
        # get the current Reward (Evaluate offhand cards!)
        negative_result = 0
        # input_cards = self.offhand
        for stich in input_cards:
            for card in stich:
                if card is not None:
                    if card.color == "R" and card.value <15 and card.value!=11 and not self.hasRedEleven(offhandCards):
                        negative_result -=1
                    if card.color == "R" and card.value <15 and card.value!=11 and self.hasRedEleven(offhandCards):
                        negative_result -=1*2
                    if not self.hasBlueEleven(offhandCards):
                        if card.color == "G" and card.value == 11:
                            negative_result -= 5
                        if card.color == "G" and card.value == 12:
                            negative_result -= 10
                    if card.color == "Y" and card.value == 11:
                        negative_result+=5
        return negative_result

    def getBinaryOptions(self, player, nu_players, nu_cards):
        #returns 0....1... x1 array BGRY 0...15 sorted
        options_list = [0]*nu_players*nu_cards
        cards        = self.getValidOptions(player)
        unique_idx   = self.cards2Idx(cards)
        for idx in unique_idx:
            options_list[idx] = 1
        return options_list



#### custom
#### custom functions very game type specific functions
#### custom
    def shiftCard(self, card_idx, current_player, next_player):
        # shift round = 0, 1, ... (for 2 shifted cards)
        #print("I shift now hand idx", card_idx, "from", self.players[current_player].name, "to", self.players[next_player].name)
        card = self.players[current_player].hand.pop(card_idx) # wenn eine Karte weniger index veringern!
        self.players[next_player].take_hand.append(card)


    def getShiftPlayer(self):
        # works FOR 4 Players only!
        if self.shift_option==0:
            return self.getNextPlayer_()
        elif self.shift_option==1:
            return self.getPreviousPlayer(self.active_player)
        elif self.shift_option==2: # opposide
            return self.getPreviousPlayer(self.getPreviousPlayer(self.active_player))
        else:
            print("ERROR!!!! TO BE IMPLEMENTED!")
            raise

    def getShiftOptions(self):
        # Return all options to shift 2 not unique card idx.
        # returns:  [[0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [0, 7], [0, 8], [0, 9], [0, 10], [0, 11], [0, 12], [0, 13], [0, 14], [1, 2], [1
        n   = len(self.players[self.active_player].hand)
        i   = 0
        options = []
        for j in range(0, n-1):
            tmp = i
            while tmp<n-1:
                options.append([j, tmp+1])
                tmp +=1
            i = i+1
        return options
