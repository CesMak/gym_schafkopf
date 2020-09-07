This repro contains a python gym environment for the card game schafkopf (sheep head).

In order to test the gym as well as training a Neuronal Network using Proximal Policy Optimization check the **Tutorials**.

You can play and test your trained neuronal network at **https://idgaming.de/**.

## Rules of Schafkopf
* Regeln hier: https://www.schafkopfschule.de/files/inhalte/dokumente/Spielen/Regeln/Schafkopfregeln-Aktuell-29.3.2007.pdf
* Langer (8 Karten):
  * Ramsch, Solo (Farbe, Wenz, Geier), Hochzeit, Ruf, Bettel, Aufgelegter Bettel, Solo Du
  * Herz ist Trumpf bei Bettel, Hochzeit, Ruf, Ramsch
  * Herz ass kann niemals gerufen werden
  * Hochzeit ist höher als Solo?
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
* phase2: ramsch (wenn alle), solo=(farbe, geier wenz), ruf(mit wem?)

 (hoechstes gewinnt) (hoechstes gewinnt)
## Installation
```bash
git clone git@github.com:CesMak/gyms.git
sudo apt install python-pip
sudo apt install python3-venv
python3 -m venv gym_env
source gym_env/bin/activate
#optional: alias ss_gym='cd ~/witches; source ../gym_env/bin/activate'
pip3 install -r requirements.txt # the requirements.txt file is in the Tutorials folder
```

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


### 01_TODO


## Further Notes
```bash
pip freeze > requirements.txt
# to export class model graph:
#sudo apt install pylint
pyreverse -o png gameClasses.py witches.py
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
|2020.08.14| added more testes and fixed game Logic bugs | fixed_gameLogic_Bugs  |
next step: check why colorFree not working


## TODO
-
