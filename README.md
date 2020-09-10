This repro contains a python gym environment for the card game schafkopf (sheep head).

In order to test the gym as well as training a Neuronal Network using Proximal Policy Optimization check the **Tutorials**.

You can play and test your trained neuronal network at **https://idgaming.de/**.

## Rules of Schafkopf
* Regeln sehr ähnlich wie hier: https://www.schafkopfschule.de/files/inhalte/dokumente/Spielen/Regeln/Schafkopfregeln-Aktuell-29.3.2007.pdf
* Langer (8 Karten):
  * Ramsch, Solo (Farbe, Wenz, Geier), Hochzeit, Ruf, Bettel, Aufgelegter Bettel, Solo Du
  * Herz ist Trumpf bei Bettel, Hochzeit, Ruf, Ramsch
  * Herz ass kann niemals gerufen werden
  * Hochzeit ist nicht höher als Solo!
  * Ruf ass muss immer gelegt werden außer:
    + Wenn der Mitspieler mindestens vier Karten mit der Ruf-Sau in der Ruf-Farbe besitzt, kann er davonlaufen (unter der Ruf-Sau ausspielen), solange die Farbe noch nicht gespielt war und er noch alle vier Farbkarten in der Hand hält.
    + Nachdem die Ruf-Farbe bereits einmal gespielt war (und durch Davonlaufen nicht zugegeben wurde), kann die Ruf-Sau gespielt oder geschmiert werden. Wurde die Ruf-Sau nicht gesucht, so darf sie erst im letzten, dem 8. Stich, zugegeben werden. Der Mitspieler, der die Ruf-Sau hat, kann diese zu jedem Zeitpunkt anspielen, sofern er an der Reihe ist.

## Kosten
* Normal(5), Schneider(+5extra), Schneider-Schwarz(+10extra)
* Solo: 15
* Bettel: 10
* Hochzeit: (Ergebnis x2)
* Laufende (ab 3 Ober)
* Ramsch: (einer zahlt alles, bei mehreren verlierern aufgeteilt, wenn alle gleich kostet 0

## Ablauf
* Declarations
* phase1: weg, solo, bettel, ruf, hochzeit
* phase2: ramsch (wenn alle), solo=(farbe, geier, wenz), ruf(mit wem?)

## Installation
```bash
git clone git@github.com:CesMak/gym_schafkopf.git
sudo apt install python-pip
sudo apt install python3-venv
python3 -m venv gym_env
source gym_env/bin/activate
pip3 install -r requirements.txt # the requirements.txt file is in the Tutorials folder
```

## State Representation
* state = np.asarray([on_table+ on_hand+ played+ play_options+ add_states+matching+decl_options+[self.active_player]])
* Example for 8 Cards and 4 Players
* Total Cards = 32
  * Each card has a color **E**ichel, **G**ruen, **H**erz, **S**chelle
  * A value: 7, 8, 9, **U**nter, **O**ber, **K**ing, 10, **A**ss
  * An index: 0...31
  * All cards sorted by index are:
  ```
  [7 of E_0, 8 of E_1, 9 of E_2, U of E_3, O of E_4, K of E_5, 10 of E_6, A of E_7, 7 of G_8, 8 of G_9, 9 of G_10, U of G_11, O of G_12, K of G_13, 10 of G_14, A of G_15, 7 of H_16, 8 of H_17, 9 of H_18, U of H_19, O of H_20, K of H_21, 10 of H_22, A of H_23, 7 of S_24, 8 of S_25, 9 of S_26, U of S_27, O of S_28, K of S_29, 10 of S_30, A of S_31]
  ```
* on_table, on_hand, played, play_options = 32x1 binary vector
  * e.g. play_options
  ```
  Options Max: [U of E_3, O of E_4, 7 of G_8, K of G_13, 10 of G_14, U of H_19, 7 of S_24, O of S_28]
  Vector list: [0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
  ```
  * 1 means this card is available as option
* The state for a player is given as:
  * card_state = on_table+ on_hand+ played+ play_options (4*32x1) = 128x1
  * add_states = [would win(1x1), colorfree(4x1), trumpfree(1x1)] (4*6x1) (3=for each other player than current) = 18x1  
    * would win is only 1 for the other player that would win the current stich
  * matching   = (4x1)
    * active player = 0  and matching = [1, 0, 1, 0]
    * this means active player is in the team with itself and player 2
  * state(150x1)=card_state + add_states+matching+decl_options

## Install gym environment
```bash
cd gym
pip install -e .
```

## Tutorials
In order to successful run the tutorials make sure to install the requirements.txt file:
```bash
pip3 install -r requirements.txt # the requirements.txt file is in the Tutorials folder
```

### 00_GameLogicTests

Simply run the unittests to test the gameLogic of Schafkopf:

```bash
/gym_schafkopf/gym-schafkopf/gym_schafkopf$ python gameLogicTests.py
```

### 01_GenerateGymData

```bash
/01_Tutorials/01_GenerateGymData$ python test_gym.py
```
### 02_GenerateBatches

Generate Data which is used later on to train a policy.
```bash
/01_Tutorials/02_GenerateBatches$ python gen_batches.py
```

```
Creating model: Schafkopf-v1
Model state  dimension: 155
Model action dimension: 36
Number of steps in one game: 9

Max RL  played wrong ai_action 23 for phase declaration
	 Reward:  -100 Done: True
Lea RL  played wrong ai_action 11 for phase declaration
	 Reward:  -100 Done: True
Jo RL  played wrong ai_action 4 for phase declaration
	 Reward:  -100 Done: True

One Batch:
Actions: [23]
State  : [array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0,
       0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0,
       0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1,
       0])]
Rewards: [-100]
LogProb: [0.2]
Done   : [True]
State: 155
State for Max
	 on_table []
	 on_hand [7 of E_0, U of E_3, K of E_5, A of E_7, 7 of H_16, K of H_21, A of H_23, 9 of S_26]
	 played []
	 options []
	 partners: Max_0(you) play with
	 Add_state for  Lea
	 	  would_win 1 is free of trump 0 color(EGHZ) free [0 0 0 0]
	 Add_state for  Jo
	 	  would_win 1 is free of trump 0 color(EGHZ) free [0 0 0 0]
	 Add_state for  Tim
	 	  would_win 1 is free of trump 0 color(EGHZ) free [0 0 0 0]
	 Declaration options [1 0 0 1]
None

Benchmark playing 100000 steps
Took: 0:01:08.550217 Number of batches:  99982
```

### 03_Parallel_Batch_Generation
* uses ray for parallel batch generation
* pip install ray==0.8.1
* is 2.5xfaster
```bash
/01_Tutorials/03_Parallel_Batch_Generation$ python gen_batches_parallel.py.py
```

```
Creating model: Schafkopf-v1
Model state  dimension: 155
Model action dimension: 36

Benchmark playing 10000 games
Took: 0:00:29.501962 Number of batches:  99925
```

### 04_Policy_PPO
* include training a neuronal network
* included classes ActorModel, ActorCritic, PPO
```bash
pip install torch
pip install onnx
pip install onnxruntime
```

* As you can see in the output below the batch size is slowly increasing
* The learning rate (lr) remains constant
* The network learns slowly correct actions (playing correct cards)

```bash
/01_Tutorials/03_Parallel_Batch_Generation$ python gen_batches_parallel.py.py
```

TODO teste ob checkt mit wem zusammenspielt....

Output:
```
...

```

## Further Notes
```bash
pip freeze > requirements.txt
# to export class model graph:
#sudo apt install pylint
pyreverse -o png gameClasses.py schafkopf.py
```

## General gym design


## Changelog
|Date|Description|commit|
|-|---------|-|
|2020.08.14| | init  |
|2020.08.14| | testing_random_playing  |
|2020.08.14| included_declarations see gameLogicTests | included_declarations  |
|2020.08.14| included rewarding and final money for ruf | added_money_ruf  |
|2020.08.14| included trump free| added_trump_free  |
|2020.09.06| added more testes and fixed game Logic bugs | fixed_gameLogic_Bugs  |
|2020.09.07| added test_color free test | added_color_test  |
|2020.09.07| added printStatetest|   |
|2020.09.08| included declarations in env environment| env_step1   |
|2020.09.08| included playing phase in env environment| env_step2  |
|2020.09.08| 8/8gameLogicTests run without error | env_step3  |
|2020.09.10| added tut2 and included cp in state | included_cp_in_state  |
|2020.09.10| added tut3 started with tut4 | added_tutorial3  |

playUntilAI -> include step dass declaration phase auch macht!

next: how to integrate schafkopf in the webpage?
