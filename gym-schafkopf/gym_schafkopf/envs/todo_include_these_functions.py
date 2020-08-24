import os
import random
import numpy as np
import onnxruntime
from idg.multiplayer.gameClasses import card, deck, player, game
from idg.config import Config
import json

# required for Rooms...:
from flask import session
from datetime import datetime

from idg import db, bcrypt
from idg.models import User, Room, Score
from idg.users.elo import getResultPlayers

'This class is a wrapper for gameClasses converts everything to right format for playing online'
class Helper():
    def __init__(self, deckType, options):
        self.options = options
        self.deckType= deckType
        if self.options is not None:
            self.game    = self.createGame()
        self.moves   = 0
        self.cardsSend = False

    def createGame(self):
        if self.deckType == "witches":
            return game(self.options)

    def convertCard2Print(self, in_card):
        'incomming: yellow_7 -> *y*7*e*'
        in_card = in_card.replace("yellow_", "*y*")
        in_card = in_card.replace("red_", "*r*")
        in_card = in_card.replace("blue_", "*b*")
        in_card = in_card.replace("green_", "*g*")
        in_card+="*e*"
        return in_card

    def getId(self, input_name):
        for j, i in enumerate(self.game.names_player):
            if i==input_name:
                return j
        return -1

    def shiftingFinished(self, rewards):
        if rewards["ai_reward"] is not None:
            self.moves +=1
            if self.moves == self.maxShiftCards:
                return True
        return False

    def getHandWebCards(self, player_):
        if self.deckType == "witches":
            return self.convertCards(self.game.players[player_].hand)

    def getOffHandCards(self, player_):
        if self.deckType == "witches":
            tmp = [item for sublist in  self.game.players[player_].offhand for item in sublist]
            return self.convertCards(tmp)

    def getShiftDirection(self):
        if self.game.shift_option == 0:
            return "left"
        elif self.game.shift_option == 1:
            return "right"
        elif self.game.shift_option == 2:
            return "opposite/ 2 left"

    def playCard(self, idx, player_):
        'player_ here as integer!'
        if self.deckType == "witches":
            if player_==self.game.active_player:
                handIdx      = self.game.idx2Hand(idx, player_)
                if handIdx is None:
                    print("Error - hand Idx is none!!! - ")
                handCard     = self.convertCards([self.game.players[player_].hand[handIdx]])
                valid_options_idx = self.game.getValidOptions(player_)# hand index
                card_options      = [self.game.players[player_].hand[i].idx for i in valid_options_idx]

                if idx in card_options:
                    rewards, round_finished, gameOver = self.game.step(handIdx)
                else:
                    print(idx, "is not in: ", card_options)
                    print("valid_options_idx:", valid_options_idx, handCard)
                    rewards        = {"ai_reward": None}
                    round_finished = False
                    gameOver       = False
            else:
                print(player_, idx, "actual it should be:", self.game.active_player)
                return {"ai_reward": None}, False, False, None, None
            return rewards, gameOver, round_finished, handIdx, handCard

    def getPlayerFromName(self, player_name):
        for j, name in enumerate(self.options["names"]):
            if name == player_name:
                return j
        return -1

    def getRandom(self):
        if self.game.shifting_phase:
            hand_card = self.game.getRandomCard()
        else:
            hand_card = self.game.getRandomValidOption()
        current_player = self.game.active_player
        return self.game.players[current_player].hand[hand_card].idx

    def selectAction(self, file_name=""):
        # action is a hand card index or???
        # Version 2.0 shifting active do not use nn, mcts anymore!
        value = 0
        current_player = self.game.active_player
        if "RL"  in self.game.player_type[current_player]:
            state = self.game.getState().flatten().astype(np.int)
            if len(file_name)==0:
                #print("\n\n CAUTION I CANNOT GET FILENAME I USE STANDARD PATH:", file_name)
                file_name = str(Config.IDG_PATH)+"/RL_Models/"+"witches_4_players_default"+".onnx"
            # else:
            #     print("custom path used.....")

            #TODO check if file really exists here?!
            #print(rel_path+"PPO_noLSTM_18893600_-0.09858012170385395_4930_-1.4972"+".onnx")
            action, value = self.rl_onnx(state, file_name)
            if action==-1:
                #print("CAUTION PlAY AS RANDOM NOW.... onnx path not valid for 4 players....")
                action = self.getRandom()
        elif "RANDOM"  in self.game.player_type[current_player]:
            #print("NO RL but RANDOM MOVE NOW!")
            action = self.getRandom()
        else:
            #print("Error - Human has to move now!")
            action = -1
        return action, value

    def checkInputs(self, state, path):
        ort_session = onnxruntime.InferenceSession(path)
        inputs      = ort_session.get_inputs()[0].shape[0]
        if  inputs == len(state):
            return 1, ""
        return 0, "Your should have "+str(len(state))+ " inputs, but you have "+str(inputs)

    def rl_onnx(self, state, path):
        '''Input:

        state:      255 list binary values for 4 players!
        path    *.onnx (with correct model)'''
        ort_session = onnxruntime.InferenceSession(path)
        if ort_session.get_inputs()[0].shape[0] == len(state):
            ort_inputs  = {ort_session.get_inputs()[0].name: np.asarray(state, dtype=np.float32)}
            ort_outs    = ort_session.run(None, ort_inputs)
            actions, value = ort_outs[0], ort_outs[1]
            # unnormalize the reward??! --> aber was ist r.mean(), r.std() ?? immer anders?!
            max_value = (np.amax(actions))
            result = np.where(actions == max_value)
            return result[0][0], round(value[0],3)
        else:
            print("Error wrong inputs! in rl_onnnxxxxxxxx")
            return -1, 0.0

    def stepAI(self, filename=""):
        action, value  = self.selectAction(filename)
        current_player = self.game.active_player
        handIdx        = self.game.idx2Hand(action, current_player)
        if handIdx is None: # invalid card moves
            return None, None, None, None, None, None
        handCard       = self.convertCards([self.game.players[current_player].hand[handIdx]])
        rewards, round_finished, gameOver =self.game.step(handIdx)

        # Je kleiner der value desto besser
        # Im letzen Zug:
        # Wenn =1 -> Spieler hat -Punkte gemacht
        # Wenn <1 -> Spieler hat Plus punkte gemacht oder 0 (z.B. 0.99)
        # FRAGE: Wird nur bewertet wie gut ein Zug war oder der Systemzustand?!

        return value, rewards, gameOver, round_finished, handIdx, handCard

    def benchmark(self, file_name, nu_test_games=1000):
        #        # function used in users->utils to test 100 games!
        #game must be like this:
        # test = Helper("witches", {"names": ["Max", "Lea", "Jo", "Tim"], "type": ["RL", "RANDOM", "RANDOM", "RANDOM"], "nu_shift_cards": 2, "nu_cards": 15, "seed": None})# Helper("witches", )
        mean_bot      = 0.0
        mean_random   = 0.0
        moves         = 17
        nu_player     = 4
        current_scores= [800]*nu_player
        game_rewards  =[0]*nu_player
        episode_counter = 0
        nu_win          = 0
        nu_draw         = 0
        nu_loss         = 0
        #nu_test_games = 1000 # set to 500 only for testing to 5
        for i in range(moves*nu_player*nu_test_games):
            val, rewards, go, ro, _, _ = self.stepAI(file_name)
            if val is None:
                print("inside none!!!!")
                return -1, _, _, nu_win, nu_draw, nu_loss
            if go:

                #scoring:
                if episode_counter == 4:
                    episode_counter = 1
                    current_scores, stats = getResultPlayers(game_rewards, current_scores)
                    result_ai = stats[0]
                    if result_ai==1.0:
                        nu_win +=1
                    elif result_ai == 0.5:
                        nu_draw +=1
                    else:
                        nu_loss +=1
                    game_rewards  =[0]*nu_player
                else:
                    episode_counter +=1
                    for m in range(len(game_rewards)):
                        game_rewards[m] += rewards["final_rewards"][m]
                mean_bot += rewards["final_rewards"][0]
                self.game.reset()
        if round(current_scores[0], 2) is None:
            return -1, _, _, nu_win, nu_draw, nu_loss
        return 1, mean_bot/nu_test_games, round(current_scores[0], 2), nu_win, nu_draw, nu_loss

    def convertColor2Witches(self, input_color):
        if input_color == "blue": return "B"
        if input_color == "green": return "G"
        if input_color == "red": return "R"
        if input_color == "yellow": return "Y"
        return None

    def convertCards(self, inputCards):
        webCards = []
        if self.deckType == "witches":
            for i in inputCards:
                color = "blue"
                if i.color == "B": color = "blue"
                if i.color == "G": color = "green"
                if i.color == "R": color = "red"
                if i.color == "Y": color = "yellow"
                player = self.getPlayerFromName(i.player)
                #print(i.player, i, WebCard(color, i.value, self.deckType, player, True, idx = i.idx))
                webCards.append(WebCard(color, i.value, self.deckType, player, i.player, True, idx = i.idx))
        return webCards

    def webCards2Dict(self, webcards):
        tmp = []
        for card in webcards:
            tmp.append(card.getDict())
        return tmp

    def getOnTableCards(self):
        tmp = []
        if self.game.shifting_phase:
            for player in self.game.players:
                tmp.extend(player.take_hand)
        else:
            tmp = self.game.on_table_cards
        return self.convertCards(tmp)

class WebCard():
    def __init__(self, suit, rank, deckType, player, player_name, visible, idx=None):
        self.suit     = suit
        self.rank     = rank
        self.type     = deckType # witches, etc.
        self.player   = player # which player holds the card (not the name!)
        self.player_name = player_name
        self.visible  = visible # does the card faceDown
        self.idx      = idx # unique card index

    def __repr__(self):
    	return str("{}_{}".format(self.suit, self.rank))

    def getDict(self):
        return {"suit": self.suit, "rank": self.rank, "type": self.type, "player": self.player, "player_name": self.player_name}

# These are the different screens that the users can be seeing
# to be deleted not used any more:
class RoomState:
  WAIT_ALL_CONNECTED = 'roomScreen' # Wait for all Players to be ready...
  ALL_CONNECTED      = 'playScreen'

class Rooms():
    def __init__(self):
        self.reset()

    def loadRooms(self):
        rooms = Room.query.all()
        for room in rooms:
            self.rooms[room.id] = room

    def getRoom(self, user):
        return Room.query.get(user.room_id)

    def getRoombyId(self, id):
        return Room.query.get(id)

    def deatachallPlayersFromRoom(self, input_user):
        # detach all users from that room except host user!
        # todo send broadcast if not in that room anymore?!
        input_id = input_user.room_id
        users = User.query.all()
        if input_id== 10000:
            print("Error is alreay a detached room the input user refers to")
            return
        for user in users:
            if user.room_id == input_id and user.username != input_user.username:
                print("detach now:", user)
                user.room_id = 10000
        # in reset set host user to not ready!
        input_user.isReady = False
        db.session.commit()

    def deleteBotsFromRoomId(self, room_id):
        users = User.query.all()
        for user in users:
            if user.type =="RL" and user.room_id == room_id:
                print("deleted this bot "+user.username+" from this room: "+str(user.room_id))
                user.room_id = 10000
        #db.session.commit()

    def isHumanLeft(self, room):
        humans  = []
        for u in room.users:
            if u.type =="HUMAN":
                humans.append(u)
        if len(humans)>0:
            return True, humans[0]
        return False, None

    def getNuBots(self, room):
        nuBots = 0
        for u in room.users:
            if u.type =="RL":
                nuBots+=1
        return nuBots

    def deleteRoomId(self, id):
        room = Room.query.get(id)
        if not id==10000:
            try:
                Room.query.filter(Room.id == id).delete()
                for u in room.users:
                    # detach also this player from the room:
                    u.room_id = 10000
                db.session.commit()
            except Exception as e:
                print("this occurs if you are in game and try to delete a room....")
                print(e)
        else:
            print("Room you try to delete does not exist!")

    def deleteRoom(self, user):
        self.deleteRoomId(user.room_id)
        db.session.commit()

    def detachPlayerFromItsRoom(self, user):
        room = Room.query.get(user.room_id)

        if room is None: # in case you are at /play site and want to logout!
            return

        curr_room_id = room.id

        # detach
        user.room_id = 10000
        db.session.commit()
        room.updateNuPlayers()

        if user.username == room.host:
            # CHANGING THE HOST IS TOOO DIFFICULT
            # cause a new room hast to be created using socket io....
            # isleft, first_human = self.isHumanLeft(room)
            # if isleft:
            #     room.host = first_human.username
            # else: # only bots left in the room
            self.deleteRoomId(curr_room_id)
            db.session.commit()
            return None
        db.session.commit()
        return room # new room obj with new host!

    def getInactiveIds(self, room_id, inactive_for_s=10):
        room              = Room.query.get(room_id)
        if room is None:
            return None
        r_users           = room.users
        inactive_ids      = []
        for user in r_users:
            if user.is_enabled and not user.is_admin and user.type == "HUMAN":
                td_last_visit =  datetime.now()-user.last_visit
                if td_last_visit.seconds>inactive_for_s and td_last_visit.seconds<3*inactive_for_s:   # 3 min
                    inactive_ids.append([1, user.username, td_last_visit.seconds]) # warning
                elif td_last_visit.seconds>3*inactive_for_s:
                    inactive_ids.append([2, user.username, td_last_visit.seconds]) # kicked out!
        return inactive_ids

    def updateTime(self, user):
        if user.type == "HUMAN":
            user.last_visit = datetime.now()
            db.session.commit()


    def reset(self):
        self.roomLimit  = 100
        self.rooms      = {}
        self.joinedIdClick = None

    def findEmptyRoomId(self):
        counter = 0
        while counter in self.rooms:
            counter +=1
        return counter

    def getJoinId(self, name):
        ' <button id="join" name="join" type="submit" value="0">join</button>'
        tmp = name.split("value=")[1].split("<join")[0]
        tmp = str(tmp).replace(">join</button>", "").replace("\"","")
        if len(tmp)==0:
            return None  # clicked on create room
        else:
            self.joinedIdClick = int(tmp)
            return int(tmp) # clicked on join with that id!

    def getIdbyName(self, name):
        ' returns session id for a username none if does not exist'
        for counter in range(self.roomLimit):
            if counter in self.rooms:
                room = self.rooms[counter]
                if room.hasUser(name):
                    print("webcard player_exists:", name, counter, room)
                    return room
        return None

    def roomExists(self, name):
        room = self.getIdbyName(name)
        if room is not None:
            return True
        else:
            return False

    def createRoom(self, username):
        user    = self.getUser(id=0, username=username)[0]
        room_id = 10000
        if user is not None:
            room_id = user.room_id
            # check if that room exists:
            room = Room.query.get(room_id)
            if room is None:
                room_id = 10000

        if room_id != 10000:
            return None
        else:
            id     = self.addRoom()
            self.appendUser2Room(id, username, setHost=True)
            return id

    def getUser(self, id=0, username=None, email=None, password=None):
        'if not none it is queryed by that!'
        if id==0   and username is not None:
            return User.query.filter_by(username=username).all()
        elif id==1 and email is not None:
            return User.query.filter_by(email=email).all()
        elif id==2 and password is not None:
            return User.query.filter_by(password=password).all()
        elif id==3 and username is not None and email is not None:
            return User.query.filter_by(username=username, email=email).all()
        else:
            return None

    def addRoom(self):
        id = self.findEmptyRoomId()
        db.session.add(Room(id=id))
        db.session.commit()
        return id

    def appendUser2Room(self, room_id, username, setHost=False):
        # the user is assigned to that new room!
        #1. find that user
        user = self.getUser(id=0, username=username)[0]
        room = Room.query.get(room_id)
        if user is not None and room.nuPlayers<room.maxPlayers and room_id != user.room_id:
            # add room_id of user:
            if setHost:
                room.host = username
            user.owner = room
            room.nuPlayers+=1
            db.session.commit()
        else:
            print("cannot append user 2 this room cause room is full!")

    def setUserReady(self, username):
        user = self.getUser(id=0, username=username)[0]
        if user is not None:
            user.isReady = True
            db.session.commit()

    def getRoomsInfo(self):
        result = {}
        for counter in range(self.roomLimit):
            if counter in self.rooms:
                room = self.rooms[counter]
                result[counter] = room.getInfo()
        return result

    def getFreeBotName(self, botType):
        users = User.query.all()
        free_bot_users = []
        for user in users:
            if user.type == "RL" and user.room_id==10000 and botType in user.username:
                free_bot_users.append(user.username)

        if len(free_bot_users)>0:
            name  = free_bot_users[random.randint(0, len(free_bot_users)-1)]
            return name
        else:
            return None
