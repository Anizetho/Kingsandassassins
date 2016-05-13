#!/usr/bin/env python3
# kingandassassins.py
# Author: Sébastien Combéfis & Anizet Thomas
# Version: Mai 13, 2016

import argparse
import json
import random
import socket
import sys

from lib import game

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


class KingAndAssassinsState(game.GameState):
    '''Class representing a state for the King & Assassins game.'''

    DIRECTIONS = {
        'E': (0, 1),
        'W': (0, -1),
        'S': (1, 0),
        'N': (-1, 0)
    }

    def __init__(self, initialstate=KA_INITIAL_STATE):
        super().__init__(initialstate)

    def _nextfree(self, x, y, dir):
        nx, ny = self._getcoord((x, y, dir))

    def update(self, moves, player):
        visible = self._state['visible']
        hidden = self._state['hidden']
        people = visible['people']
        for move in moves:
            print(move)
            # ('move', x, y, dir): moves person at position (x,y) of one cell in direction dir
            if move[0] == 'move':
                x, y, d = int(move[1]), int(move[2]), move[3]
                p = people[x][y]
                if p is None:
                    raise game.InvalidMoveException('{}: there is no one to move'.format(move))
                nx, ny = self._getcoord((x, y, d))
                new = people[nx][ny]
                # King, assassins, villagers can only move on a free cell
                if p != 'knight' and new is not None:
                    raise game.InvalidMoveException('{}: cannot move on a cell that is not free'.format(move))
                if p == 'king' and BOARD[nx][ny] == 'R':
                    raise game.InvalidMoveException('{}: the king cannot move on a roof'.format(move))
                if p in POPULATION.union({'assassin'}) and player != 0:
                    raise game.InvalidMoveException('{}: villagers and assassins can only be moved by player 0'.format(move))
                if p in {'king', 'knight'} and player != 1:
                    raise game.InvalidMoveException('{}: the king and knights can only be moved by player 1'.format(move))
                # Move granted if cell is free
                if new is None:
                    people[x][y], people[nx][ny] = people[nx][ny], people[x][y]
                # If cell is not free, check if the knight can push villagers
                else:
                    pass
            # ('arrest', x, y, dir): arrests the villager in direction dir with knight at position (x, y)
            elif move[0] == 'arrest':
                if player != 1:
                    raise game.InvalidMoveException('arrest action only possible for player 1')
                x, y, d = int(move[1]), int(move[2]), move[3]
                arrester = people[x][y]
                if arrester != 'knight':
                    raise game.InvalidMoveException('{}: the attacker is not a knight'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target not in POPULATION:
                    raise game.InvalidMoveException('{}: only villagers can be arrested'.format(move))
                visible['arrested'].append(people[tx][ty])
                people[tx][ty] = None
            # ('kill', x, y, dir): kills the assassin/knight in direction dir with knight/assassin at position (x, y)
            elif move[0] == 'kill':
                x, y, d = int(move[1]), int(move[2]), move[3]
                killer = people[x][y]
                if killer == 'assassin' and player != 0:
                    raise game.InvalidMoveException('{}: kill action for assassin only possible for player 0'.format(move))
                if killer == 'knight' and player != 1:
                    raise game.InvalidMoveException('{}: kill action for knight only possible for player 1'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target is None:
                    raise game.InvalidMoveException('{}: there is no one to kill'.format(move))
                if killer == 'assassin' and target == 'knight':
                    visible['killed']['knights'] += 1
                    people[tx][tx] = None
                elif killer == 'knight' and target == 'assassin':
                    visible['killed']['assassins'] += 1
                    people[tx][tx] = None
                else:
                    raise game.InvalidMoveException('{}: forbidden kill'.format(move))
            # ('attack', x, y, dir): attacks the king in direction dir with assassin at position (x, y)
            elif move[0] == 'attack':
                if player != 0:
                    raise game.InvalidMoveException('attack action only possible for player 0')
                x, y, d = int(move[1]), int(move[2]), move[3]
                attacker = people[x][y]
                if attacker != 'assassin':
                    raise game.InvalidMoveException('{}: the attacker is not an assassin'.format(move))
                tx, ty = self._getcoord((x, y, d))
                target = people[tx][ty]
                if target != 'king':
                    raise game.InvalidMoveException('{}: only the king can be attacked'.format(move))
                visible['king'] = 'injured' if visible['king'] == 'healthy' else 'dead'
            # ('reveal', x, y): reveals villager at position (x,y) as an assassin
            elif move[0] == 'reveal':
                if player != 0:
                    raise game.InvalidMoveException('raise action only possible for player 0')
                x, y = int(move[1]), int(move[2])
                p = people[x][y]
                if p not in hidden['assassins']:
                    raise game.InvalidMoveException('{}: the specified villager is not an assassin'.format(move))
                people[x][y] = 'assassin'
        # If assassins' team just played, draw a new card
        if player == 0:
            visible['card'] = hidden['cards'].pop()
            statecard = visible['card']

    def _getcoord(self, coord):
        return tuple(coord[i] + KingAndAssassinsState.DIRECTIONS[coord[2]][i] for i in range(2))

    def winner(self):
        visible = self._state['visible']
        hidden = self._state['hidden']
        # The king reached the castle
        for doors in visible['castle']:
            coord = self._getcoord(doors)
            if visible['people'][coord[0]][coord[1]] == 'king':
                return 1
        # The are no more cards
        if len(hidden['cards']) == 0:
            return 0
        # The king has been killed
        if visible['king'] == 'dead':
            return 0
        # All the assassins have been arrested or killed
        if visible['killed']['assassins'] + len(set(visible['arrested']) & hidden['assassins']) == 3:
            return 1
        return -1

    def isinitial(self):
        return self._state['hidden']['assassins'] is None

    def setassassins(self, assassins):
        self._state['hidden']['assassins'] = set(assassins)

    def prettyprint(self):
        visible = self._state['visible']
        hidden = self._state['hidden']
        result = ''
        if hidden is not None:
            result += '   - Assassins: {}\n'.format(hidden['assassins'])
            result += '   - Remaining cards: {}\n'.format(len(hidden['cards']))
        result += '   - Current card: {}\n'.format(visible['card'])
        result += '   - King: {}\n'.format(visible['king'])
        result += '   - People:\n'
        result += '   +{}\n'.format('----+' * 10)
        for i in range(10):
            result += '   | {} |\n'.format(' | '.join(['  ' if e is None else e[0:2] for e in visible['people'][i]]))
            result += '   +{}\n'.format(''.join(['----+' if e == 'G' else '^^^^+' for e in visible['board'][i]]))
        print(result)

    @classmethod
    def buffersize(cls):
        return BUFFER_SIZE


class KingAndAssassinsServer(game.GameServer):
    '''Class representing a server for the King & Assassins game'''

    def __init__(self, verbose=False):
        super().__init__('King & Assassins', 2, KingAndAssassinsState(), verbose=verbose)
        self._state._state['hidden'] = {
            'assassins': None,
            'cards': random.sample(CARDS, len(CARDS))
        }

    def _setassassins(self, move):
        state = self._state
        if 'assassins' not in move:
            raise game.InvalidMoveException('The dictionary must contain an "assassins" key')
        if not isinstance(move['assassins'], list):
            raise game.InvalidMoveException('The value of the "assassins" key must be a list')
        for assassin in move['assassins']:
            if not isinstance(assassin, str):
                raise game.InvalidMoveException('The "assassins" must be identified by their name')
            if not assassin in POPULATION:
                raise game.InvalidMoveException('Unknown villager: {}'.format(assassin))
        state.setassassins(move['assassins'])
        state.update([], 0)

    def applymove(self, move):
        try:
            state = self._state
            move = json.loads(move)
            if state.isinitial():
                self._setassassins(move)
            else:
                self._state.update(move['actions'], self.currentplayer)
        except game.InvalidMoveException as e:
            raise e
        except Exception as e:
            print(e)
            raise game.InvalidMoveException('A valid move must be a dictionary')


class KingAndAssassinsClient(game.GameClient):
    '''Class representing a client for the King & Assassins game'''

    def __init__(self, name, server, verbose=False):
        super().__init__(server, KingAndAssassinsState, verbose=verbose)
        self.__name = name

    def _handle(self, message):
        pass



    def _nextmove(self, state):
        # Two possible situations:
        # - If the player is the first to play, it has to select his/her assassins
        #   The move is a dictionary with a key 'assassins' whose value is a list of villagers' names
        # - Otherwise, it has to choose a sequence of actions
        #   The possible actions are:
        #   ('move', x, y, dir): moves person at position (x,y) of one cell in direction dir
        #   ('arrest', x, y, dir): arrests the villager in direction dir with knight at position (x, y)
        #   ('kill', x, y, dir): kills the assassin/knight in direction dir with knight/assassin at position (x, y)
        #   ('attack', x, y, dir): attacks the king in direction dir with assassin at position (x, y)
        #   ('reveal', x, y): reveals villager at position (x,y) as an assassin # reveal = révéler

        state = state._state['visible']

        # To find the position of a person
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


        # First card
        if state['card'] is None:

            # To recognize an assassin
            def recognizeassassins() :
                P = state['people']
                A1 = P[2][1]
                A2 = P[5][5]
                A3 = P[8][3]
                posAssassins = [A1, A2, A3]
                return posAssassins

            global posAssassins
            posAssassins = recognizeassassins()

            return json.dumps({'assassins': posAssassins}, separators=(',', ':'))


        # Other cards
        else:
            # To play with the villagers and the assassins
            if self._playernb == 0:

                # Part to move the villagers and assassins

                def recognizeassassins() :
                    P = state['people']
                    A1 = P[2][1]
                    A2 = P[5][5]
                    A3 = P[8][3]
                    posAssassins = [A1, A2, A3]
                    return posAssassins

                # To take only 2 villagers whom will move
                def take2villagers() :
                    V = state['people']
                    V1 = V[9][5]
                    V2 = V[7][5]
                    posVillagers = [V1, V2]
                    return posVillagers

                # One assassin will kill a knight at the position (3,0)
                def killknight() :
                    # The Assassin's name (posAssassins[0]) allows to find its position
                    Assassinskiller = findpos(posAssassins[0])
                    Assassinskilleraction = []
                    Assassinskillerpathfirst = ['W']
                    Assassinskillerpathsecond = ['S']
                    Assassinskillerpathbugs = ['N','S','N','S','N','S','N','S','N','S','N','S','N','S' ]
                    global pathAssassinskillersfirst, pathAssassinskillerssecond
                    pathAssassinskillersfirst = Assassinskillerpathfirst
                    pathAssassinskillersfirst = Assassinskillerpathsecond
                    pathAssassinskillersbugs = Assassinskillerpathbugs
                    posknighthigh = state['people'][3][0]
                    otherassassins = findpos(posAssassins[1])
                    if posknighthigh == 'knight' :
                        # During the first round
                        if otherassassins == (5,5):
                            Assassinskilleraction.append(('move', Assassinskiller[0], Assassinskiller[1], pathAssassinskillersfirst[0]))
                            del(pathAssassinskillersfirst[0])
                        # During the second round
                        elif otherassassins == (6,5):
                            Assassinskilleraction.append(('kill', Assassinskiller[0], Assassinskiller[1], pathAssassinskillerssecond[0]))
                            del(pathAssassinskillerssecond[0])
                        # After the second round, to avoid the bugs...
                        else :
                            Assassinskilleraction.append(('move', Assassinskiller[0], Assassinskiller[1], pathAssassinskillersbugs[0]))
                            del(pathAssassinskillersbugs[0])
                    else :
                        # the assassin turns around to avoid the bugs...
                        Assassinskilleraction.append(('move', Assassinskiller[0], Assassinskiller[1], pathAssassinskillersbugs[0]))
                        del(pathAssassinskillersbugs[0])

                    return Assassinskilleraction

                # Assassin (in (5,5)) --> if the king goes beside of him, he kills the king !
                #                     --> Else a villager (3,4) moves alone to avoid bugs...
                def Assassin1Space():
                    posking = findpos('king')
                    global posAssassins
                    posAssassins = recognizeassassins()
                    posAssassins1 = findpos(posAssassins[1])
                    posy = posAssassins1[0]
                    posx = posAssassins1[1]
                    Assassin1action = []
                    global posVillagers
                    posVillagers = take2villagers()
                    posVillagers1 = findpos(posVillagers[0])
                    Villagerpath = ['N','S','N','S','N','S','N','S','N','S','N','S','N','S','N']
                    global pathV
                    pathV = Villagerpath
                    if posking == (5,4):
                        Assassin1action.append(('kill', posy, posx, 'W'))
                    else:
                        Assassin1action.append(('move',posVillagers1[0],posVillagers1[1], pathV[0]))
                        del(pathV[0])

                    return Assassin1action

                # Assassin (in (8,3)) --> if the king goes beside of him, he kills the king !
                #                     --> Else a villager moves alone to avoid bugs...
                def Assassin2Space():
                    posking = findpos('king')
                    global posAssassins
                    posAssassins = recognizeassassins()
                    posAssassins2 = findpos(posAssassins[2])
                    posy = posAssassins2[0]
                    posx = posAssassins2[1]
                    space = [(posy-1, posx) , (posy, posx-1),(posy, posx+1) , (posy+1, posx)]
                    Assassin2action = []
                    global posVillagers
                    posVillagers = take2villagers()
                    posVillagers2 = findpos(posVillagers[1])
                    Villagerpath = ['E','W','E','W','E','W','E','W','E','W','E','W','E','W','E']
                    global pathV
                    pathV = Villagerpath
                    if posking in space:
                        if posking == (8,4):
                            Assassin2action.append(('kill', posy, posx, 'E'))
                        elif posking == (9,3):
                            Assassin2action.append(('kill', posy, posx, 'S'))
                        elif posking == (8,2):
                            Assassin2action.append(('kill', posy, posx, 'W'))
                        elif posking == (7,3):
                            Assassin2action.append(('kill', posy, posx, 'N'))
                        else:
                            Assassin2action.append(('move',posVillagers2[0],posVillagers2[1], pathV[0]))
                            del(pathV[0])
                    else :
                        Assassin2action.append(('move',posVillagers2[0],posVillagers2[1], pathV[0]))
                        del(pathV[0])

                    return Assassin2action

                actionASSORVILL1 = killknight()[0]
                actionASSORVILL2 = Assassin1Space()[0]
                actionASSORVILL3 = Assassin2Space()[0]

                return json.dumps({'actions': [actionASSORVILL1, actionASSORVILL2, actionASSORVILL3]}, separators=(',', ':'))



            # To play with the king and the knights
            else:
                # Part to move the knights

                # To determinate the 4 knights whom will move (only those 4 knights.. To be sure with the AP_Knight --> trick...)
                def the4Knights():
                    posKnight = findpos('knight')
                    kn1 = posKnight[6]
                    kn2 = posKnight[3]
                    kn3 = posKnight[4]
                    kn4 = posKnight[5]
                    pos4knights = [kn1, kn2, kn3, kn4]
                    return pos4knights

                # To determinate the moves of the knights
                def knightmove():
                    postheKnight = the4Knights()
                    postheKnight1 = postheKnight[0]
                    postheKnight2 = postheKnight[1]
                    postheKnight3 = postheKnight[2]
                    postheKnight4 = postheKnight[3]
                    knightaction1 = []
                    knightaction2 = []
                    knightaction3 = []
                    knightaction4 = []
                    i=0
                    # The knights have all a predefined path...
                    knight1path = ['W','W','W','W','W','W','W','N','N','N','N','W','N','N','W','W']
                    knight2path = ['W','W','W','W','W','N','N','N','N','N','N','W']     # On the fifth move : arrest or one move to the right
                    knight3path = ['W','W','W','W','W','N','N','N','N','N','N','W']
                    knight4path = ['W','W','W','W','W','N','N','N','N','N','N','W']
                    global path1, path2, path3, path4
                    path1 = knight1path
                    path2 = knight2path
                    path3 = knight3path
                    path4 = knight4path
                    knightaction = []
                    while i < 1:
                        knightaction1.append(('move', postheKnight1[0], postheKnight1[1], path1[0]))
                        knightaction2.append(('move', postheKnight2[0], postheKnight2[1], path2[0]))
                        knightaction3.append(('move', postheKnight3[0], postheKnight3[1], path3[0]))
                        knightaction4.append(('move', postheKnight4[0], postheKnight4[1], path4[0]))
                        del(path1[0])
                        del(path2[0])
                        del(path3[0])
                        del(path4[0])
                        knightaction = [knightaction1[0], knightaction2[0], knightaction3[0], knightaction4[0]]
                        i += 1
                    return knightaction

                # Part to move the king

                # To know the squares around the king
                def kingSpace(kingState):
                    posy = findpos('king')[0]
                    posx = findpos('king')[1]
                    space = [(posy-1, posx-1) , (posy-1, posx) , (posy-1, posx+1) , (posy, posx-1),
                             (posy, posx+1) , (posy+1, posx-1) , (posy+1, posx) , (posy+1, posx+1)]

                    if kingState == 'healthy' or kingState == 'injured':
                        spacefinal = []
                        for squares in space:
                            if squares[0] < 10 and squares[1] < 10:
                                spacefinal.append(squares)
                        return spacefinal

                # To know if, on the squares around the king, there are villagers
                def KingInDanger():
                        espace = kingSpace('healthy')
                        for squares in espace :
                            if PEOPLE[squares[0]][squares[1]] in POPULATION :
                                return True
                            else:
                                return False

                # To determinate the moves of the king
                def kingmove():
                    posKing = findpos('king')
                    kingaction = []
                    i=0
                    # The king can only do one path..  :'(
                    kingpath = ['W', 'W', 'W', 'W', 'W', 'N', 'N', 'N', 'N', 'N', 'W', 'W', 'W']
                    global path
                    path = kingpath
                    while i < 1:
                        # If, on the squares around the king, there are no villagers
                        if KingInDanger() is False :
                            kingaction.append(('move', posKing[0], posKing[1], path[0]))
                        else:
                            kingaction.append(())
                        del(path[0])
                        i += 1
                    return kingaction

                actionKNIGHT1 = knightmove()[0]
                actionKNIGHT2 = knightmove()[1]
                actionKNIGHT3 = knightmove()[2]
                actionKNIGHT4 = knightmove()[3]
                actionKING = kingmove()[0]
                return json.dumps({'actions': [actionKNIGHT1, actionKNIGHT2, actionKNIGHT3, actionKNIGHT4, actionKING]}, separators=(',', ':'))

# The program doesn't work anymore after the "Turn #3".
# The problem is that the function del() doesn't delete the elements that I require and so the first moves (for king and knights) come back everytime.
# I wanted to make something that works when I run this in the terminal : so my code is basic.
# With this code, I did several mistakes/ :
# 1) I don't consider the PA but I don't exceed the PA on a card :
# For the king, I give only one move ; for the knights, I give 4 moves ; for the villagers and assassins, I give 3 moves.
# 2) I don't do the difference between the ground and the roof
# It was great to do this code ! Unfortunately, it should have been better if we could start this project earlier.

if __name__ == '__main__':
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='King & Assassins game')
    subparsers = parser.add_subparsers(
        description='server client',
        help='King & Assassins game components',
        dest='component'
    )

    # Create the parser for the 'server' subcommand
    server_parser = subparsers.add_parser('server', help='launch a server')
    server_parser.add_argument('--host', help='hostname (default: localhost)', default='localhost')
    server_parser.add_argument('--port', help='port to listen on (default: 5000)', default=5000)
    server_parser.add_argument('-v', '--verbose', action='store_true')
    # Create the parser for the 'client' subcommand
    client_parser = subparsers.add_parser('client', help='launch a client')
    client_parser.add_argument('name', help='name of the player')
    client_parser.add_argument('--host', help='hostname of the server (default: localhost)',
                               default=socket.gethostbyname(socket.gethostname()))
    client_parser.add_argument('--port', help='port of the server (default: 5000)', default=5000)
    client_parser.add_argument('-v', '--verbose', action='store_true')
    # Parse the arguments of sys.args
    args = parser.parse_args()

    if args.component == 'server':
        KingAndAssassinsServer(verbose=args.verbose).run()
    else:
        KingAndAssassinsClient(args.name, (args.host, args.port), verbose=args.verbose)