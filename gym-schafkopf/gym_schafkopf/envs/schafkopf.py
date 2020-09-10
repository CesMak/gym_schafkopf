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
        self.decl_options   = ["weg", "ruf_E", "ruf_G", "ruf_S"] # , "hochzeit", "bettel", "solo"
        self.solo_options   = []             # ["solo_e", "solo_g", "solo_h", "solo_s", "geier", "wenz"]
        self.declarations   = []
        self.phase          = "declaration"  # declaration, (contra, retour), playing
        # dummy initiatlization is necessary for matching! (do not change otherwise schafkopf_env will not work)
        self.matching       = {"type": "ruf_G", "partner": 0}   # type: Ramsch, Solo, Hochzeit, Bettel, Ruf, partners: index of partner to caller, spieler: index of spieler
        super().setup_game()       # is required here already for gym to work!
        self.correct_moves     = 0

    def reset(self):
        self.nu_games_played +=1

        self.players           = []  # stores players object
        self.on_table_cards    = []  # stores card on the table
        self.played_cards      = []  # of one game # see also in players offhand!
        self.gameOver          = 0
        self.rewards           = np.zeros((self.nu_players,))
        self.current_round     = 0
        super().setup_game()
        self.active_player     = self.nextGamePlayer()
        self.correct_moves     = 0
        self.declarations      = []
        for i in range (self.nu_players):
            self.declarations.append("")

    def DeclarationFinished(self):
        for i in self.declarations:
            if len(i)==0:
                return False
        return True

    def assignDeclaration(self, cards, player_idx, decl="", use_random=False):
        #random.seed(None)
        if use_random:
            valid_options = self.getPossDeclarations(cards)
            self.declarations[player_idx] = valid_options[random.randrange(len(valid_options))]
        else:
            self.declarations[player_idx] = decl

    def randomInitDeclarations(self):
        for i in range(self.nu_players):
            self.assignDeclaration([self.players[i].hand], i, use_random=True)

    def getWinningDeclaration(self, actual, new_decl):
        if self.decl_options.index(new_decl)>self.decl_options.index(actual):
            return True
        return False

    def getHighestDeclaration(self, declarations):
        # simplify declarations
        highest = "weg"
        idx     = 0
        for i, decl in enumerate(declarations):
            if self.getWinningDeclaration(highest, decl):
                highest = decl
                idx     = i
        return highest, idx

    def getPossDeclarations(self, cards):
        declarations = []
        for i in self.decl_options:
            if "hochzeit" in i:
                trumps = self.getTrumps(cards)
                if len(trumps)==1:
                    declarations+=["hochzeit"]
            elif not "hochzeit" in i:
                declarations.append(i)
        return declarations

    def setTrickOrder(self, trump="H", lead_color=""):
        trick_order = []
        if "ruf" in self.matching["type"] or "hochzeit" in self.matching["type"] or "ramsch" in self.matching["type"] or "solo" in self.matching["type"]:
            for i in ["O", "U"]:
                for j in ["E", "G", "H", "S"]:
                    trick_order.append(self.idxOfName(i, j))
            for i in ["A", "10", "K", "9", "8", "7"]:
                trick_order.append(self.idxOfName(i, trump))
            if len(lead_color) != 0:
                for i in ["A", "10", "K", "9", "8", "7"]:
                    trick_order.append(self.idxOfName(i, lead_color))
            other_cols  = ["E", "G", "H", "S"]
            others_cols = other_cols.remove(trump)
            if len(lead_color) != 0:
                others_cols = other_cols.remove(lead_color)
            for z in other_cols:
                for i in ["A", "10", "K", "9", "8", "7"]:
                    trick_order.append(self.idxOfName(i, z))
        #print(super().idxList2Cards(list(reversed(trick_order))))
        self.matching["order"] = list(reversed(trick_order))

    def setDeclaration(self, prev_declarations, solo_decl="", ruf_decl="", use_random=True):
        # set matching
        # type = ramsch, solo_farbe, ruf_farbe, wenz, geier
        # spieler = player index
        # partner of the caller
        #input prev_declarations from phase 1 see getPossDeclarations

        if use_random and "solo" in self.decl_options:
            solo_decl = self.solo_options[random.randrange(len(self.solo_options))]

        highest, idx = self.getHighestDeclaration(prev_declarations)

        if use_random and "ruf" in self.decl_options:
            ruf_decl  = self.getRufDeclarations([self.players[idx].hand])
            ruf_decl  = ruf_decl[random.randrange(len(ruf_decl))]

        if highest=="solo":
            self.matching["type"]    = solo_decl
            #TODO:
            self.matching["trump"]   = "H"
        elif highest=="weg":
            self.matching["type"]    = "ramsch"
        elif highest=="ruf":
            self.matching["type"]    = ruf_decl
            self.matching["partner"] = self.getPlayerIdxOfSpecificCard("A", ruf_decl.split("_")[1])
        else: # hochzeit, bettel
            self.matching["type"]    = highest

        self.matching["spieler"]     = idx
        self.matching["trump"]       = "H"

        self.setTrickOrder(trump=self.matching["trump"])

        if "ruf" in self.matching["type"]:
            tmp                   = [self.matching["spieler"], self.matching["partner"]]
            players_ruf           = [self.players[i].hand for i in tmp]
            players_ruf           = [item for sublist in players_ruf for item in sublist]

            enemys                = list(range(4))
            enemys                = [i for j, i in enumerate(enemys) if j not in tmp]
            enemys                = [self.players[i].hand for i in enemys]
            enemys                = [item for sublist in enemys for item in sublist]

            ruf_laufende   = self.getNuLaufende(players_ruf)
            enemy_laufende = self.getNuLaufende(enemys)
            if ruf_laufende>enemy_laufende:
                self.matching["nuLaufende"] = ruf_laufende
            else:
                self.matching["nuLaufende"] = enemy_laufende

        if self.DeclarationFinished():
            self.phase = "playing"

    def getNuLaufende(self, cards):
        counter        = 0
        for idx_order in reversed(self.matching["order"]):
            counter_before = counter
            for m in super().cards2Idx(cards):
                if idx_order == m:
                    counter +=1
            if counter_before == counter:
                return counter
        return counter

    def getPlayerIdxOfSpecificCard(self, value, color):
        for n, play in enumerate(self.players):
            if super().hasSpecificCard(value, color, [play.hand], doConversion=True):
                return n
        print("error in:", "getPlayerIdxOfSpecificCard", "player with that ass/card was not found???!")
        return None

    def hasColoredCard(self, cards, color, without_trumpfs=True):
        for card in cards:
            my_list = ["7", "8", "9", "U", "O", "K", "10", "A"]
            if without_trumpfs:
                my_list = ["7", "8", "9", "K", "10", "A"]
            for i in my_list:
                if super().hasSpecificCard(i, color, cards, doConversion=True):
                    return True
        return False

    def getColoredCards(self, cards, color):
        return self.getAnyCards(cards, colors=[color], values=["7", "8", "9", "K", "10", "A"])

    def getRufDeclarations(self, cards):
        declarations = []
        for card in cards:
            for color in ["E", "G", "S"]:
                if self.hasColoredCard(cards, color) and not super().hasSpecificCard("A", color, cards, doConversion=True):
                    declarations.append("ruf_"+color)
        return declarations

    def convertRufDeclarations2Binary(self, list_decl):
        #list_decl e.g. ["ruf_G", "ruf_E"]
        result = [0.0]*4
        for i in range(4):
            for j in list_decl:
                if "ruf_E" in j:   result[0]=1.0
                elif "ruf_G" in j: result[1]=1.0
                elif "ruf_S" in j: result[2]=1.0
                else:
                    result[i] = 0.0
        return result

    def getAnyCards(self, cards, colors=["E", "G", "H", "S"], values=["7", "8", "9", "K", "10", "A"]):
        found_cards = []
        for card in cards:
            for value in values:
                for color in colors:
                    card = super().getSpecificCard(value, color, cards, doConversion=True)
                    if card is not None:
                        found_cards.append(card)
        return found_cards

    def getTrumps(self, cards, trump_color="H"):
        trump_cards = []
        if trump_color is not None:
            trump_cards+= self.getAnyCards(cards, colors=["H"])
        trump_cards+= self.getAnyCards(cards, values=["U", "O"])
        return trump_cards

    def isTrump(self, card, trump_color="H"):
        a = self.getTrumps([[card]], trump_color)
        if len(a)>0:
            return True, a[0]
        else:
            return False, None

    def getInColor(self, cards):
        # returns the leading color of the on_table_cards
        # trump
        # or color is returned
        if len(cards)==0:
            return None
        else:
            first_card = cards[0]
            isTrump, _     = self.isTrump(first_card, self.matching["trump"])
            if isTrump:
                return "trump"
            else:
                return first_card.color

    def getOptions(self, incolor, player, orderOptions=False):
        # return hand position of this card
        # incolor is None if there is no card yet on the table
        # incolor is trump if o or u or trump color is played
        # incolor is color = E, G, S if color is played!
        options      = []
        if self.phase =="declaration":
            return options
        elif self.phase =="playing":
            cards        = self.players[player].hand

            if incolor is None:
                for i, card in enumerate(cards):
                    options.append(i)
            else:
                if incolor == "trump":
                    trumps = self.getTrumps([cards])
                    #print("in trump,", trumps, player, incolor, cards)
                    if len(trumps) == 0:
                        options = list(range(len(cards)))
                        self.players[player].setTrumpFree()
                    else:
                        for i in trumps:
                            options.append(super().idx2Hand(i.idx, player))
                else: # color is played
                    col_cards = self.getColoredCards([cards], incolor)
                    #print(incolor, player, col_cards)
                    if len(col_cards) == 0:
                        options = list(range(len(cards)))
                        self.players[player].setColorFree(incolor)
                    else:
                        for i in col_cards:
                            options.append(super().idx2Hand(i.idx, player))

            if orderOptions: return sorted(options, key = lambda x: ( x[1].color,  x[1].value))

            # get options for ruf game:
            if "ruf" in self.matching["type"] and self.matching["partner"] == player:
                called_color = self.matching["type"].split("_")[1]

                # wenn ruf farbe angespielt wird muss partner die Ass reinspielen:
                if not len(options)>3 and incolor == called_color: # sonst davonlaufen
                    #try to get ass
                    cards = super().hand2Cards(player, options)
                    card = super().getSpecificCard("A", called_color, [cards], doConversion=True)
                    if card is not None: return [super().idx2Hand(card.idx, player)]

                # wenn keine Karte angespielt ist darf rufspieler eine andere Karte der ruffarbe nicht spielen (außer das Ass)
                # außer er kann davonlaufen
                elif incolor is None:
                    # delete ruf card options except eichel of options
                    new_options = []
                    cards = super().hand2Cards(player, options)
                    for j in cards:
                        if not called_color == j.color:
                            new_options.append(j)
                    ass_card = super().getSpecificCard("A", called_color, [cards], doConversion=True)
                    if ass_card is not None:
                        new_options.append(ass_card)
                        options = []
                        for i in new_options:
                            options.append(super().idx2Hand(i.idx, player))
                        return options
                    else: # ass is already played do not change anything:
                        return options
            return options

    def getValidOptions(self, cards, player):
        # cards = ontable cards!
        options = self.getOptions(self.getInColor(cards), player) # hand index
        # return as cards
        return [self.players[player].hand[i] for i in options]

    def evaluateWinner(self):
        #uses on_table_cards to evaluate the winner of one round
        #returns winning card
        #player_win_idx: player that one this game! (0-3)
        #on_table_win_idx: player in sequence that one!
        highest_value    = 0
        winning_card     = self.on_table_cards[0]

        if "ruf" in self.matching["type"] or "hochzeit" in self.matching["type"] or "ramsch" in self.matching["type"]:
            # do a reordering according to incolor! (otherwise eichel beats green etc.)
            incolor = self.getInColor(self.on_table_cards)
            if incolor is not None and incolor != "trump" and incolor != self.matching["trump"]:
                self.setTrickOrder(trump=self.matching["trump"], lead_color=incolor)
            for i, card in enumerate(self.on_table_cards):
                rank = self.matching["order"].index(card.idx)
                if card is not None and rank > highest_value:
                    highest_value = rank
                    winning_card = card
                    on_table_win_idx = i
            player_win_idx = self.player_names.index(winning_card.player)
        else: # solo
            print("TODO")
        #print("inside evaluate_winner", winning_card, on_table_win_idx, player_win_idx)
        return winning_card, on_table_win_idx, player_win_idx


    def playUntilAI(self, print_=False):
        rewards        = {"state": "play_or_shift", "ai_reward": None}
        gameOver       = False
        round_finished = False
        while len(self.players[self.active_player].hand) > 0:
            current_player = self.active_player
            if "RANDOM" in self.player_types[current_player]:
                card            = self.getRandomValidOption()
                hand_idx_action = self.players[self.active_player].hand.index(card)
                if print_:
                    print("[{}] {} {}\t plays {}\tCard {}\tHand Index {}\t len {} ->colFree {} trumpFree {}".format(self.current_round, current_player, self.player_names[current_player], self.player_types[current_player], card, hand_idx_action, len(self.players[current_player].hand), self.players[current_player].colorFree, self.players[current_player].trumpFree))
                rewards, round_finished, gameOver = self.step(hand_idx_action, print_)
                if print_ and round_finished:
                    print("")
            else:
                return rewards, round_finished, gameOver
        return rewards, True, True

    def step(self, action_idx, print_=False):
        #Note that card_idx is a Hand Card IDX!
        # it is not card.idx unique number!
        # Not that in this function action is not checked if correct / possible (this is done in play_ai_move)
        round_finished = False
        if self.phase == "declaration" and action_idx>31:
            self.assignDeclaration([], self.active_player, decl=self.decl_options[action_idx-32])
            if self.DeclarationFinished():
                self.phase = "playing"
                round_finished = True
                self.setDeclaration(self.declarations)
            self.active_player = self.getNextPlayer()
            return {"state": self.phase, "ai_reward": 0, "on_table_win_idx": None, "trick_rewards": None, "player_win_idx": None, "final_rewards": self.rewards}, round_finished, False
        elif self.phase == "playing" and action_idx<=31:
            played_card = self.players[self.active_player].hand.pop(action_idx)
            self.on_table_cards.append(played_card)
            # Case round finished:
            trick_rewards    = [0]*self.nu_players
            on_table_win_idx = -1
            player_win_idx   = -1
            if len(self.on_table_cards) == self.nu_players:
                winning_card, on_table_win_idx, player_win_idx = self.evaluateWinner()
                trick_rewards[player_win_idx] = self.countResult([self.on_table_cards])
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
                self.getPoints(print_)
                for i in range(len(self.total_rewards)):
                    self.total_rewards[i] +=self.rewards[i]

    		#yes this is the correct ai reward in case all players are ai players.
            return {"state": self.phase, "ai_reward": trick_rewards[player_win_idx], "on_table_win_idx": on_table_win_idx, "trick_rewards": trick_rewards, "player_win_idx": player_win_idx, "final_rewards": self.rewards}, round_finished, self.isGameFinished()
        else:
            print("ERROR", self.phase, action_idx)
            return None
    def countResult(self, input_cards):
        #input_cards = [[card1, card2, card3, card4], [stich2], ...]
        # in class player
        result = 0
        for stich in input_cards:
            for card in stich:
                if card is not None:
                    for cards_value, value in zip(["A", "10", "K", "O", "U"], [11, 10, 4, 3, 2]):
                        if (str(card.getConversion())) == cards_value:
                            result += value
                            break
        return result

    def getPoints(self, print_=False):
        # according to self.rewards get the final Points and store them in the rewards!
        if "ruf" in self.matching["type"]:
            players_ruf           = [self.matching["spieler"], self.matching["partner"]]
            enemys                = list(range(4))
            enemys                = [i for j, i in enumerate(enemys) if j not in players_ruf]

            ruf_points            = 0
            ruf_names             = []
            ruf_wins              = 0
            money                 = 5

            for j in players_ruf:
                ruf_names.append(self.players[j].name)
                ruf_points  += self.rewards[j]
            if ruf_points>60:
                ruf_wins = 1

            # get costs of this game:
            if ruf_wins:
                tmp = ruf_points
            else:
                tmp = 120-ruf_points

            if tmp>90:
                money+=5
            if tmp==120:
                money+=5

            # TODO assign ober etc.
            if self.matching["nuLaufende"]>2:
                money +=self.matching["nuLaufende"]*5

            if not ruf_wins:
                money*=-1

            for j in players_ruf:
                self.rewards[j] = money
            for i in enemys:
                self.rewards[i] = money*-1

            if print_:
                print("")
                print(self.matching["type"]+": "+ruf_names[0]+" called "+ruf_names[1])
                print("poitns", ruf_points, "--> money: ", money)
                print("Rewards:", self.rewards)

    def getState(self):
        play_options = self.getBinaryOptions(self.active_player, self.nu_players, self.nu_cards)
        decl_options = self.getBinaryDeclarations(self.active_player)

        #play_options = self.convertAvailableActions(play_options)
        on_table, on_hand, played = self.getmyState(self.active_player, self.nu_players, self.nu_cards)
        add_states = [] #(nu_players-1)*5
        for i in range(len(self.players)):
            if i!=self.active_player:
                # this calls evaluate_winner 3 times! - this is too much!
                # TODO once should be enough!
                add_states.extend(self.getAdditionalState(i))

        # append matching here!
        matching = self.getMatchingBinary(self.active_player)
        return np.asarray([on_table+ on_hand+ played+ play_options+ add_states+matching+decl_options+[self.active_player]])

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

    def getBinaryDeclarations(self, player):
        # return     32          = weg
        #            33,34,35,36 = ruf_e, ruf_g, ruf_h, ruf_s
        options = [0.0]*len(self.decl_options)
        options[0] = 1.0   # weg is always an option!
        if self.phase =="declaration":
            allowed_decl =   self.getRufDeclarations([self.players[player].hand])
            # assign ruf options:
            for i in range(1,4):
                for j in allowed_decl:
                    if "ruf_E" in j:   options[1]=1.0
                    elif "ruf_G" in j: options[2]=1.0
                    elif "ruf_S" in j: options[3]=1.0
                    else:
                        options[i] = 0.0
        return options

    def getBinaryOptions(self, player, nu_players, nu_cards):
        #returns 0....1... x1 array BGRY 0...15 sorted
        options_list = [0.0]*nu_players*nu_cards
        cards        = self.getValidOptions(self.on_table_cards, self.active_player)
        if len(cards)>0:
            unique_idx   = self.cards2Idx(cards)
            for idx in unique_idx:
                options_list[idx] = 1.0
        return options_list

    def getMatchingBinary(self, playeridx):
        matching = [0.0]*self.nu_players
        if not "spieler" in self.matching:
            # declarations have not been made!
            return matching
        else:
            if "ruf" in self.matching["type"] or "hochzeit" in self.matching["type"]:
                players_ruf           = [self.matching["spieler"], self.matching["partner"]]
                enemys                = list(range(4))
                enemys                = [i for j, i in enumerate(enemys) if j not in players_ruf]
                if self.matching["spieler"] == playeridx or self.matching["partner"] == playeridx:
                    matching[self.matching["spieler"]] = 1.0
                    matching[self.matching["partner"]] = 1.0
                else:
                    for i in enemys:
                        matching[i] = 1.0
            elif "ramsch" in self.matching["type"]:
                if self.matching["spieler"] == playeridx:
                    matching[playeridx] = 1.0
        return matching

    def getAdditionalState(self, playeridx):
        # result = [would win, eghs color free, trump free]=6x1
        # for only enemy players result=18x1 vector
        result = []
        player = self.players[playeridx]

        #extend if this player would win the current cards
        player_win_idx = playeridx
        if len(self.on_table_cards)>0:
            winning_card, on_table_win_idx, player_win_idx = self.evaluateWinner()
        if player_win_idx == playeridx:
            result.extend([1.0])
        else:
            result.extend([0.0])
        result.extend(player.colorFree)
        result.append(player.trumpFree)
        return result

    def play_ai_move(self, ai_action, print_=False):
        '''
        ai_action idx from 0....31 = card index
        32 = weg
        33,34,35 = ruf_E, ruf_G, ruf_S
        '''
        cp    =  self.active_player
        if "RL" in self.player_types[cp]:
            if self.phase == "declaration" and ai_action>31:
                allowed_decl = self.getBinaryDeclarations(cp)
                if print_: print(self.player_names[cp], self.player_types[cp],"trys to declare....", ai_action," allowed is", allowed_decl)
                if allowed_decl[ai_action-32] == 1.0:
                    self.correct_moves +=1
                    rewards, round_finished, gameOver = self.step(ai_action, print_)
                    if print_:
                        print("\t "+self.player_names[cp]+": "+self.declarations[cp])
                        if self.DeclarationFinished():
                            print("\t Highest Declaration: "+str(self.getHighestDeclaration(self.declarations)))
                            print("\t Matching           : ", str(self.matching)[0:60],"\n")
                else:
                    print("this declaration is not allowed! - ERROR", allowed_decl)
                    return {"state": "play_or_shift", "ai_reward": None}, False, True
            elif self.phase == "playing" and ai_action<=31:
                card_options__    = self.getValidOptions(self.on_table_cards, cp)
                card              = self.idx2Card(ai_action)
                player_has_card   =super().hasSpecificCard(card.value, card.color, [self.players[cp].hand], doConversion=False)
                tmp               = card.idx
                card_options      = self.cards2Idx(card_options__)

                if player_has_card and tmp in card_options:
                    if print_:
                        print(self.current_round, str(cp)+"-"+self.player_names[cp], self.player_types[cp],"plays", card)
                    self.correct_moves +=1
                    rewards, round_finished, gameOver = self.step(self.idx2Hand(tmp, cp), print_)
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
            else:
                if print_: print(self.player_names[cp], self.player_types[cp], " played wrong ai_action", ai_action, "for phase", self.phase)
                return {"state": "play_or_shift", "ai_reward": None}, False, True

            return rewards, round_finished, gameOver
        else:
            print("I am not an RL PlAYER..... ERROR")
            return {"state": "play_or_shift", "ai_reward": None}, False, True # rewards round_finished, game_over













######
####  currently not used functions:::
####




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

    def getRandomPossCards(self, list, nuCards):
        #random.seed(None)
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


    def convertTakeHand(self, player, take_hand):
        converted_cards = []
        for card in take_hand:
            card.player = player.name
            converted_cards.append(card)
        return converted_cards
