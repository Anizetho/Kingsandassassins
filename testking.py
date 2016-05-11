import argparse
import json
import random
import socket
import sys

#from lib import game

BUFFER_SIZE = 2048

CARDS = (
    # (AP King, AP Knight, Fetter, AP Population/Assassins)
    # True on peut emprisonner ; False on peut pas emprisonner
    # 1er chiffre = déplacement roi
    # 2ème chiffre = déplacement chevalier
    # 3 ème chiffre = déplacement citoyens (et parmis eux les assassins)
    (1, 6, True, 5),
    (1, 5, False, 4),
    (1, 6, True, 5),
    (1, 6, True, 5),
    (1, 5, True, 4),
    (1, 5, False, 4),
    (2, 7, False, 5),
    (2, 7, False, 4),
    (1, 6, True, 5),
    (1, 6, True, 5),
    (2, 7, False, 5),
    (2, 5, False, 4),
    (1, 5, True, 5),
    (1, 5, False, 4),
    (1, 5, False, 4)
)

# Nom de tous les citoyens
POPULATION = {
    'monk', 'plumwoman', 'appleman', 'hooker', 'fishwoman', 'butcher',
    'blacksmith', 'shepherd', 'squire', 'carpenter', 'witchhunter', 'farmer'
}

# Plateau du jeu :
# R représente les toits ; G représente le sol
BOARD = (
    ('R', 'R', 'R', 'R', 'R', 'G', 'G', 'R', 'R', 'R'),
    ('R', 'R', 'R', 'R', 'R', 'G', 'G', 'R', 'R', 'R'),
    ('R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'R'),
    ('R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'),
    ('R', 'G', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('G', 'G', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'R', 'R', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G'),
    ('R', 'R', 'G', 'G', 'G', 'G', 'G', 'G', 'G', 'G')
)

# Coordinates of pawns on the board
# Emplacement des chevaliers (7) et des citoyens (12)
# les coordonnées (x, y) donnent d'abords la colonne (x) et ensuite la ligne (y)
KNIGHTS = {(1, 3), (3, 0), (7, 8), (8, 7), (8, 8), (8, 9), (9, 8)}
VILLAGERS = {
    (1, 7), (2, 1), (3, 4), (3, 6), (5, 2), (5, 5),
    (5, 7), (5, 9), (7, 1), (7, 5), (8, 3), (9, 5)
}

# Separate board containing the position of the pawns
PEOPLE = [[None for column in range(10)] for row in range(10)]

# Place the king in the right-bottom corner
PEOPLE[9][9] = 'king'

# Place the knights on the board
for coord in KNIGHTS:
    PEOPLE[coord[0]][coord[1]] = 'knight'

# Place the villagers on the board
# random.sample(A, len(A)) returns a list where the elements are shuffled
# this randomizes the position of the villagers
# Les citoyens ont des places définies sur le plateau cependant ces places ne sont pas attribuées à des citoyens en particulier d'où le random
for villager, coord in zip(random.sample(POPULATION, len(POPULATION)), VILLAGERS):
    PEOPLE[coord[0]][coord[1]] = villager




KA_INITIAL_STATE = {
    'board': BOARD,
    'people': PEOPLE,
    # Castle représente les 2 entrées où doit aller le roi
    'castle': [(2, 2, 'N'), (4, 1, 'W')],
    'card': None,
    'king': 'healthy',
    'lastopponentmove': [],
    'arrested': [],
    'killed': {
        'knights': 0,
        'assassins': 0
    }
}

# Trouver la position d'un pion
def findpos(name):
    l = 0
    listknight = []
    for line in PEOPLE:
        l += 1
        c = 0
        for column in line :
            c += 1
            if column == name :
                if name == 'knight':
                    listknight.append((l-1, c-1))
                else:
                    return l-1, c-1
    return listknight

#print('positions :')
#pos = findpos('king')
#posl = pos[0]-1
#posc = pos[1]
#print(pos)
#print(posl)
#print(posc)
#print(" ")

def dangerousforking():
    posking = findpos('king')
    print(posking)
    autour = [[(posking[0]-1 , posking[1]-1),(posking[0]-1, posking[1]), (posking[0]-1, posking[1]+1)],[(posking[0], posking[1]-1),(posking[0], posking[1]), (posking[0], posking[1]+1)], [(posking[0]+1 , posking[1]-1),(posking[0]+1, posking[1]), (posking[0]+1, posking[1]+1)]]
    for elem in autour:
        print(elem)



print(dangerousforking())
print(" ")



#def APcards():
#    AP_King = state['card'][0]
#    AP_Knight = state['card'][1]
#    AP_Villager_ = state['card'][3]
#    APall = [AP_King, AP_Knight, AP_Villager_]
#    return APall

#PA = APcards()
#print(PA)
#print(" ")


#def recognizeassassins() :
#    P = PEOPLE
#    A1 = P[2][1]
#    A2 = P[5][5]
#    A3 = P[8][3]
#    posAssassins = [A1, A2, A3]
#    return posAssassins

#print(KA_INITIAL_STATE['people'])
#posAssassins = recognizeassassins()
#test1 = posAssassins[0]
#print(posAssassins)
#print(test1)

