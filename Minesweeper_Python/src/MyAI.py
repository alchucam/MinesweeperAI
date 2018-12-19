# ==============================CS-199==================================
# FILE:			MyAI.py
#
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#
# ==============================CS-199==================================

from AI import AI
from Action import Action
from queue import *
from collections import deque
from itertools import permutations
from copy import *
from collections import defaultdict
import math
import random


class MyAI( AI ):

        #@paramter: totalMines: total mines in the game left to be flag
        #@parammeter: rowDimension, colDimension : row and column dimension of the board
        #@paramter: startX, startY : initial revealed position when the game starts. always start with 0 value of the tile
        def __init__(self, rowDimension, colDimension, totalMines, startX, startY):

                #initial position when the game starts
                self.position = (startX, startY)
                #number of total mines of the board
                self.totalMines = totalMines
                #row dimension of the board
                self.rowDimension = rowDimension
                #column dimension of the board
                self.colDimension = colDimension
                #list for all adjacent tiles of the tile (exclude the tile location itself)
                self.adjacentTiles = list()
                #list for unopened adjacent tiles of the tile (checked with validAdjacent() function)
                self.validAdjTiles = list()
                #list for opened adjacent tiles of the tile
                self.openAdjTiles = list()
                #queue of tiles to check next. A way to track down which tiles to check next.
                self.checkQueue = deque()
                #list for temporary storing any tiles unable to perform action due to lack of information from checkQueue.
                #it will replenish checkQueue again, once checkQueue is deplenished
                self.mysteryQueue = deque()
                #A queue that contains non-bombs for sure we can perform uncover for the action.
                self.safeQueue = deque()
                #A queue that contains bombs for sure we can perform flag for the action
                self.bombQueue = deque()
                #A queue to track any unopened tiles after there are no mines in the board,
                #as it is obvious that there are no mines in these tiles.
                self.cleaningQueue = deque()
                #matrix to represent the board state.
                # each index contains a value representing the percept of the tile.
                #-2: unopened
                #-1: mine/flag
                #0-8: indicates how many bombs in the adjacentTiles.
                self.matrix = []
                #function to create our own board in matrix
                #this function is called once as a part of the constructor.
                self.boardMatrix()
                #coordinates where we'll perform action. Initalized with initial position.
                self.actionLocation = (startX, startY)
                #dict to hold the tile that has gone through the assumption and did not give out any results
                #it is used to optimize the run
                self.noAssumeList = list()


        #@parameter: number: int = percept number
        def getAction(self, number: int) -> "Action Object":

                #important: always come at the beginning of the getAction.
                #update the location in our own board matrix, by taking the stored action location and resulting percept from parameter
                self.matrix[self.actionLocation[0]][self.actionLocation[1]] = number

                #endgame cleaning.
                #if there are no mines left. add remaining unopen tiles to cleaningQueue.
                #then repeatedly uncover those tiles; afterwards, leave the game.
                if self.totalMines == 0:
                        if not self.cleaningQueue:
                                self.cleaningQueue += self.getAllUnopen()
                        if self.cleaningQueue:
                                self.actionLocation = self.cleaningQueue.popleft()
                                return Action(AI.Action.UNCOVER, self.actionLocation[0], self.actionLocation[1])
                        return Action(AI.Action.LEAVE)

                #update noAssumeList; purely for improving time efficiency.
                self.updateNoAssume()

                #add valid adjacent tiles from initial/previous action performed location to the queue
                #valid adjacent tiles represent unopened and valid board positioned neighboring tiles of the paramter tile.
                #Afterwards, add these valid adjacent tiles to the queue if any. Making sure there are no duplicate tiles in the queue as well.
                validAdj = list()
                validAdj += self.validAdjacent(self.actionLocation[0], self.actionLocation[1], self.matrix)

                #if the tile has unopen neighbors
                if validAdj:
                        tileValue = self.checkBoard(self.actionLocation[0], self.actionLocation[1], self.matrix)
                        if tileValue  == 0:
                                for val in validAdj:
                                        #checking for duplicates
                                        if val not in self.checkQueue and val not in self.safeQueue:
                                                self.safeQueue.append(val)

                        elif tileValue != -1:
                                for val in validAdj:
                                        if self.actionLocation not in self.checkQueue and self.actionLocation not in self.mysteryQueue:
                                                self.checkQueue.append(self.actionLocation)

                if self.safeQueue or self.bombQueue:
                        return self.safeOrBomb()

                #perform action on the tile popped from the queue
                #First, check percept/value of the adjacent tiles of the tile popped from the queue.
                #If there is any 0 percept in that adjacent tiles: guarantee no mines for the tile popped from the queue.
                #If there is any 1 or higher percept in that adjacent tiles: we'll put it into temporary queue to deal with it later.
                repeat = False
                count = 30

                while self.checkQueue and count > 0:
                        count -= 1
                        checkLocation = self.checkQueue.popleft()

                        if self.checkBoard(checkLocation[0], checkLocation[1], self.matrix) != -1:
                                bombLeft = self.getBombLeft(checkLocation[0], checkLocation[1], self.matrix)
                                result = self.validBombLeft(bombLeft)
                        else:
                                if not self.checkQueue and not repeat:
                                        repeat = True
                                        self.checkQueue = deepcopy(self.mysteryQueue)
                                        self.checkQueue.append(checkLocation)
                                        self.mysteryQueue.clear()
                                continue

                        if (result == 'valid'):

                                valAdj = list()
                                valAdj += self.validAdjacent(checkLocation[0], checkLocation[1], self.matrix)

                                bomb = bombLeft[1]

                                if bomb > 0:
                                        for adj in valAdj:
                                                if adj not in self.bombQueue:
                                                        self.bombQueue.append(adj)
                                elif bomb == 0:
                                        for adj in valAdj:
                                                if adj not in self.safeQueue:
                                                        self.safeQueue.append(adj)
                                if self.safeQueue or self.bombQueue:
                                        self.checkQueue += self.mysteryQueue
                                        self.checkQueue.append(checkLocation)
                                        self.mysteryQueue.clear()
                                        return self.safeOrBomb()

                        elif (result == 'unknown'):
                                if checkLocation not in self.mysteryQueue:
                                        self.mysteryQueue.append(checkLocation)


                        #empty checkQueue, but hasn't repeat,
                        #we repeat one more time.
                        if not self.checkQueue and not repeat:

                                repeat = True
                                self.checkQueue = deepcopy(self.mysteryQueue)
                                self.checkQueue.append(checkLocation)
                                self.mysteryQueue.clear()


                #pre assumption function
                #moving everything to mysteryQueue
                if self.checkQueue:
                        for c in self.checkQueue:
                                if c not in self.mysteryQueue:
                                        self.mysteryQueue.append(c)
                self.checkQueue.clear()



                #iterate through coordinates in the mysteryQueue
                if not self.checkQueue and self.mysteryQueue:

                        #preparation of priority type dictionary
                        prePQ = self.combine(self.mysteryQueue, self.matrix) #dictionary but not priority queue type yet.

                        #if we find negative value for the input of numberOfAssumptions, get None for prePQ, exit the game.
                        if prePQ is None:
                                return Action(AI.Action.LEAVE)
                        elif prePQ:
                                pQ = self.sortPriorityDictionary(prePQ) #priority type list

                                #iterate through the priority queue list
                                for pqTile in pQ:
                                        #if the tile itself is a bomb, skip
                                        if self.checkBoard(pqTile[0][0], pqTile[0][1], self.matrix) != -1:
                                                bombLeft = self.getBombLeft(pqTile[0][0], pqTile[0][1], self.matrix)
                                        else:
                                                continue
                                        if (bombLeft[0] < 0 or bombLeft[1] < 0 or bombLeft[1] > bombLeft[0]):
                                                return Action(AI.Action.LEAVE)
                                        #noa and patterns for the parameter of assume function
                                        noa = self.numberOfAssumptions(bombLeft[0], bombLeft[1])
                                        patterns = self.permutationPatterns(bombLeft[0], bombLeft[1])

                                        #the assumption function.
                                        self.assume(pqTile, noa, patterns)

                                        #if we made a successful assumption, which can be telled by replenished bombQueue or safeQueue.
                                        #put everything in the extraTiles

                                        if self.bombQueue or self.safeQueue:
                                                break


                #with the successful assumption, we clear everything
                self.checkQueue.clear()
                self.checkQueue = deepcopy(self.mysteryQueue)
                self.mysteryQueue.clear()
                if self.safeQueue or self.bombQueue:
                        return self.safeOrBomb()

                #even the assume function fails by this point, we will guess a tile to uncover.
                return self.guess(self.checkQueue, self.matrix)

        ##############end of getAction function################



        #guess function
        def guess(self, queue, board):
                finalLocationz = self.findAllUnopen()

                if len(finalLocationz) == self.totalMines:
                        for f in finalLocationz:
                                self.bombQueue.append(f)
                        return self.safeOrBomb()

                s1 = tuple()
                s2 = tuple()
                s3 = tuple()
                score = 8
                r = 1.0
                #from the queue, find the lowest remaining bomb/unopened tile ratio; least remaining bomb per unopened tiles better.
                for i in queue:
                        s1 = self.getBombLeft(i[0], i[1], board) #[0]: unopened tile, [1]: remaining bomb
                        if s1[0] == 0:
                                continue
                        if r > float(s1[1]/s1[0]):
                                r = float(s1[1]/s1[0])
                                s2 = (i[0], i[1])

                validAdjTiles = list()

                #if no such exists, guessAccum
                #case: empty queue.
                if not s2:
                        return self.guessAccum(finalLocationz)
                #if such exists, find all the unopened valid tiles,
                #from those tiles, find the number of opened neighor tiles.
                #try to find the least opened neighbor tiles.
                #if no such exists, guessAccum
                #if exists, perform uncover on that location
                validAdjTiles += self.validAdjacent(s2[0], s2[1], board)
                for i in validAdjTiles:
                        if score > len(self.openAdjacent(i[0], i[1], board)):
                                score = len(self.openAdjacent(i[0], i[1], board))
                                s3 = i
                if not s3:
                        return self.guessAccum(finalLocationz)
                self.actionLocation = s3

                return Action(AI.Action.UNCOVER, self.actionLocation[0], self.actionLocation[1])


        #return True if there is a tile that has three consecutive neighbor tiles that are bombs.
        def bombsNext(self, f0, f1, o1, XorY):
                if XorY == "Y":
                        if self.validinBoard(f0, f1) and self.validinBoard(f0, o1):
                                if self.checkBoard(f0, f1, self.matrix) == -1 and self.checkBoard(f0, o1, self.matrix) == -1:
                                        return True
                elif XorY == "X":
                        if self.validinBoard(f0, f1) and self.validinBoard(o1, f1):
                                if self.checkBoard(f0, f1, self.matrix) == -1 and self.checkBoard(o1, f1, self.matrix) == -1:
                                        return True
                return False


        #A guess function that think it is unlikely to be a bomb if there are a tile with three consecutive neighbor tiles being bombs.
        def guessAccum(self, finalLocationz):
                #finalLocationz = findAllUnopen()
                theMaxPlace = tuple()
                theMinPlace = tuple()
                theMax = 0
                theMin = 0
                bombTogether = False
                for f in finalLocationz:
                        openAdjTiles = list()
                        tempValue = 0
                        openAdjTiles = self.openAdjacent(f[0],f[1], self.matrix)

                        for o in openAdjTiles:
                                val = self.checkBoard(o[0],o[1], self.matrix)
                                if val == -1:
                                        difX = f[0] - o[0]
                                        difY = f[1] - o[1]
                                        if difX == 0 and difY != 0:
                                                if self.bombsNext(f[0]+1, f[1], o[1], "Y") or self.bombsNext(f[0]-1, f[1], o[1], "Y"):
                                                        bombTogether = True
                                                        break
                                        elif difX != -1 and difY == 0:
                                                if self.bombsNext(f[0], f[1]+1, o[0], "X") or self.bombsNext(f[0], f[1]-1, o[0], "X"):
                                                        bombTogether = True
                                                        break
                                tempValue += val

                        if bombTogether:
                                self.actionLocation = f
                                return Action(AI.Action.UNCOVER, self.actionLocation[0], self.actionLocation[1])


                #safety measure
                self.actionLocation = finalLocationz[0]
                return Action(AI.Action.UNCOVER, self.actionLocation[0], self.actionLocation[1])




        #find all unopened tiles, put the coordinate into the list, and return it.
        def findAllUnopen(self):
                finalLocationz = list()
                for x, sub_list in enumerate(self.matrix):
                        for y, value in enumerate(sub_list):
                                if value == -2:
                                        finalLocationz.append((x,y))
                return finalLocationz


        #create adjacentTiles of a coordinate.
        #put all 8 adjacent tiles of the coordinate from the parameter (excluding the coordinate itself) into a self.adjacentTiles list
        #the function checks if the tiles are inside the board.
        def checkAdjacent(self, x_coord, y_coord):
                adjacentTiles = list()
                for x in range(-1,2):
                        for y in range(-1,2):
                                if (x+x_coord >= 0 and x+x_coord < self.colDimension and y+y_coord >= 0 and y+y_coord < self.rowDimension):
                                        if (x == 0 and y == 0):
                                                continue
                                        adjacentTiles.append((x+x_coord,y+y_coord))
                return adjacentTiles


        #modify adjacentTiles to create a validAdjTiles list
        #only collects unopen adjacent tiles to the list.
        def validAdjacent(self, x, y, board):
                adjacentTiles = list()
                validAdjTiles = list()
                adjacentTiles = self.checkAdjacent(x,y)
                for val in adjacentTiles:
                        if (board[val[0]][val[1]] == -2):
                                validAdjTiles.append((val[0], val[1]))
                return validAdjTiles

        #modify adjacentTiles to create a openAdjTiles list
        #only collects already opened adjacent tiles to the list.
        def openAdjacent(self, x, y, board):
                adjacentTiles = list()
                openAdjTiles = list()
                adjacentTiles = self.checkAdjacent(x,y)
                for val in adjacentTiles:
                        if board[val[0]][val[1]] != -2:
                                openAdjTiles.append((val[0], val[1]))
                return openAdjTiles


        #getter function for board
        #returns the value of the tile.
        def checkBoard(self, x, y, board):
                return board[x][y]

        #return True if a tile exists inside the board.
        def validinBoard(self, x, y):
                if x >= 0 and x < self.colDimension and y >= 0 and y < self.rowDimension:
                        return True
                else:
                        return False

        #function to initially create the board state according to the dimensions of the game.
        #fill with -2 to all the tiles of the board
        #-2 represents unopened state in the board.
        def boardMatrix(self):
                row = []
                for i in range(self.colDimension): #[x][]
                        for j in range(self.rowDimension): #[][y]
                                row.append(-2) #-2 = unknown
                        self.matrix.append(row)
                        row = []

        #get all unopened (-2) tiles from the matrix to the appendList
        #return the appendList
        def getAllUnopen(self):
                appendList = list()
                for x, sub_list in enumerate(self.matrix):
                        for y, value in enumerate(sub_list):
                                if value == -2:
                                        appendList.append((x,y))
                return appendList


        #find the opened neighbor that is affected by openning unopened tiles of the tile
        #and double check if the newly found affected adjacent neighbors exist in the queue or not
        #if it does exist already, don't add.
        #From the position (x,y), find and return any opened neighbor tiles of (x,y) that has unopen neighbor tiles,
        #then, we check if that opened neighbor tiles is not a bomb, not in the queue, and not in the affectedAdj (for checking duplicate purpose)
        def getAffectedAdj(self, x, y, queue, board):

                affectedAdj = deque()
                openAdjTiles = self.openAdjacent(x,y,self.matrix)
                for adj in openAdjTiles:
                        validAdjTiles = list()
                        validAdjTiles = self.validAdjacent(adj[0], adj[1], self.matrix)
                        if validAdjTiles:
                                if self.checkBoard(adj[0],adj[1], board) == -1 or self.checkBoard(adj[0],adj[1], board) == -2:
                                        continue
                                if not queue:
                                        if adj not in affectedAdj:
                                                affectedAdj.append(adj)
                                elif queue:
                                        if adj not in affectedAdj and adj not in queue:
                                                affectedAdj.append(adj)
                return affectedAdj



        #if there was a change in a tile that affects a tile in the noAssumeList,
        #remove it from the List.
        def updateNoAssume(self):
                opAdj = self.openAdjacent(self.actionLocation[0], self.actionLocation[1], self.matrix)
                #remove old ones
                for noA in self.noAssumeList:
                        val = self.validAdjacent(noA[0], noA[1], self.matrix)
                        if not val:
                                self.noAssumeList.remove((noA[0], noA[1]))
                for op in opAdj:
                        if op in self.noAssumeList:
                                self.noAssumeList.remove((op[0], op[1]))


        #return a set of (unopened tile, remaining bomb)
        def getBombLeft(self, x, y, board):
                validAdjTiles = list()
                openAdjTiles = list()

                validAdjTiles += self.validAdjacent(x, y, board)
                openAdjTiles += self.openAdjacent(x, y, board)

                numUnopen = 0
                numBomb = self.checkBoard(x, y, board)

                for x in validAdjTiles:
                        numUnopen += 1
                #check for already discvoered bomb
                for x in openAdjTiles:
                        if self.checkBoard(x[0], x[1], board) == -1:
                                numBomb -= 1

                return (numUnopen, numBomb)

        #take a set of bombleft from the getBombLeft function, and figure out if it is valid
        #the set is in form of (numUnopen, numBomb)
        def validBombLeft(self, bombLeft):
                if bombLeft[0] == bombLeft[1] or bombLeft[1] == 0 :
                        return 'valid'
                elif bombLeft[1] < 0:
                        return 'invalid'
                elif bombLeft[1 > 0]:
                        return 'unknown'

        #perform any location in safeQueue or bombQueue if such locations exist
        def safeOrBomb(self):
                if self.safeQueue:
                        self.actionLocation = self.safeQueue.popleft()
                        return Action(AI.Action.UNCOVER, self.actionLocation[0], self.actionLocation[1])
                if self.bombQueue:
                        self.actionLocation = self.bombQueue.popleft()
                        self.totalMines -= 1
                        return Action(AI.Action.FLAG, self.actionLocation[0], self.actionLocation[1])

        #obtain the number of assumptions possible for the tile,
        #based on the number of unopened tiles and number of mines left
        def numberOfAssumptions(self, numberOfUnopenedTiles, numberOfMinesLeft):
                n = numberOfUnopenedTiles
                r = numberOfMinesLeft
                f = math.factorial
                value =int((f(n))/(f(r)*f(n-r)))

                return value

        #create dictionary from number of unopened tiles and number of mines left.
        def combine(self, queue, board):
                q = deque()
                priorityDictionary = dict()
                q += queue

                for element in q:
                        if self.checkBoard(element[0], element[1], board) != -1:
                                bombLeft = self.getBombLeft(element[0], element[1], board)
                        else:
                                continue
                        if element in self.noAssumeList:
                                continue
                        #making sure no negative value will be inputted for combine -> numberOfAssumptions -> factorial
                        opAdj = list()
                        opAdj += self.openAdjacent(element[0], element[1], board)
                        bombCheck = self.checkBoard(element[0], element[1], board)
                        for op in opAdj:
                                if self.checkBoard(op[0], op[1], board) == -1:
                                        bombCheck -= 1
                        if bombCheck < 0:
                                return None
                        noa = self.numberOfAssumptions(bombLeft[0], bombLeft[1])
                        if noa < 5:
                                priorityDictionary[(element[0],element[1])] = noa

                if not priorityDictionary:
                        return False
                return priorityDictionary


        #all the patterns we can make for the number of unopened tiles and number of mines left.
        def permutationPatterns(self, numberOfUnopenedTiles, numberOfMinesLeft):
                l = [None] * numberOfUnopenedTiles
                for x in range(numberOfUnopenedTiles):
                        if x < numberOfMinesLeft:
                                l[x] = -1
                        else:
                                l[x] = -2
                return list(set(permutations(l)))

        #sort dictionary argument into priority queue style in a form of list type
        def sortPriorityDictionary(self, pD):
                sorted_by_value = sorted(pD.items(), key=lambda ky: ky[1])
                return sorted_by_value



        #assumption logic
        #for a tile (mTile) along with number of patterns (noa) and all the possible patterns combination (patterns)
        #we will traverse our copied temporary board from the base pattern,
        #and repeat the process for all possible other base patterns
        #Then, we will see if there is any unopened tile that assumption function always give the same result.
        #As a result, we will know the tile can be considered as a bomb or safe based on that consistent same result.
        def assume(self, mTile, noa, patterns):

                #get the tile that we want to start assuming from priorty queue
                theTile = mTile[0] #the tile that will be the base for the assumption.
                nOa = noa #number of assumption.

                #create as many lists as number of assumption
                #the list will contain the state, (bomb or non-bomb) resulting from the assumption, of the newly openned tile
                #-3 represents opened as a part of assumption.
                #-2 represents unopened
                #-1 represents bomb/flag

                collect = dict() #holds all possible combination of values for the coordinate. key: coordinate. value: assuming tile value
                first = True #boolean flag to switch from first iteration on the possible assumption to the next following iterations
                affectedTilesTrackQueue = deque() #queue to double check, prevent duplicates in traverse.
                nextRunQueue = deque() #queue to hold tiles that were run on the first iteration; which will be used for the following iteration
                resu = True #boolean flag to keep track of if the validBombLeft function results give invalid results or not

                #loop as many as number of possible assumption.
                #first iteration:
                #next following iterations:
                for x in range(0, nOa):
                        matrixTwo = deepcopy(self.matrix) #create our own temporary board to use for assumption
                        resu = True
                        listValue = list() #list of assuming tile values for collect dictionary
                        listCoordinate = list() #list of corresponding coordinates to the listValue for collect dictionary.
                        holeList = list() #list to hold and track any tiles that we are unable to assume.

                        affectedTilesQueue = deque() #queue to pipeline tiles for traversing
                        limit = 10 #limit of how many traverse we will do from the base assumption.
                        extraFirstTiles = list()

                        #update our board with the pattern
                        validAdjTiles = list()
                        validAdjTiles += self.validAdjacent(theTile[0], theTile[1], matrixTwo)

                        for tile, adj in zip (patterns[x], validAdjTiles):
                                if (adj[0], adj[1]) not in listCoordinate and tile == -1:
                                        listCoordinate.append((adj[0], adj[1]))
                                        listValue.append(tile)
                                        matrixTwo[adj[0]][adj[1]] = -1
                                elif (adj[0], adj[1]) not in listCoordinate and tile == -2:
                                        extraFirstTiles.append(adj)

                                #update the copied matrix
                                matrixTwo[adj[0]][adj[1]] = tile


                        #first iteration
                        if first:
                                affectedTilesQueue.append((theTile[0],theTile[1]))
                        while limit > 0 and first and affectedTilesQueue:
                                nextTile = affectedTilesQueue.popleft()
                                affectedTilesTrackQueue.append(nextTile)
                                nextRunQueue.append(nextTile)
                                limit -= 1;

                                #check if the tile is a bomb. if so, move to next tile
                                if self.checkBoard(nextTile[0], nextTile[1], matrixTwo) != -1:
                                        bombLeft = self.getBombLeft(nextTile[0], nextTile[1], matrixTwo)
                                        result = self.validBombLeft(bombLeft)
                                else:
                                        continue
                                validAdj = list()
                                validAdj = self.validAdjacent(nextTile[0], nextTile[1], matrixTwo)


                                #check for validBombLeft results
                                #valid: number of bomb left is matching to the unopened neighbor tiles
                                #invalid: number of bomb left > unopened neighbor tiles; asusmption failed
                                #unknown: number of bomb left < unopened neighbor tiles; not enough information to be sure
                                #valid case: update listvalue, listCoordinate, affectedTilesQueue
                                if (result == 'valid'):
                                        affectedTilesQueue += self.getAffectedAdj(nextTile[0], nextTile[1], affectedTilesTrackQueue, matrixTwo)
                                        bomb = bombLeft[1]
                                        if bomb > 0:
                                                for adj in validAdj:
                                                        if adj not in listCoordinate:
                                                                matrixTwo[adj[0]][adj[1]] = -1
                                                                listValue.append(-1)
                                                                listCoordinate.append((adj[0],adj[1]))
                                        elif bomb == 0:
                                                for adj in validAdj:
                                                        if adj not in listCoordinate:
                                                                matrixTwo[adj[0]][adj[1]] = -3
                                                                listValue.append(-3)
                                                                listCoordinate.append((adj[0],adj[1]))

                                #assumption failed
                                elif (result == 'invalid'):
                                        resu = False
                                        break

                                #can't figure out yet, move on to the next tile
                                elif (result == 'unknown'):
                                        affectedTilesQueue += self.getAffectedAdj(nextTile[0], nextTile[1], affectedTilesTrackQueue, matrixTwo)
                                        for adj in validAdj:
                                                if adj not in listCoordinate:
                                                        holeList.append((adj[0], adj[1]))
                                                        listValue.append('u')
                                                        listCoordinate.append((adj[0], adj[1]))

                        #from second to last iteration of assumption pattern
                        if not first:
                                for nextTile in nextRunQueue:
                                        #making sure the tile is not a bomb itself.
                                        if self.checkBoard(nextTile[0], nextTile[1], matrixTwo) != -1:
                                                bombLeft = self.getBombLeft(nextTile[0], nextTile[1], matrixTwo)
                                                result = self.validBombLeft(bombLeft)
                                        else:
                                                continue

                                        validAdj = list()
                                        validAdj = self.validAdjacent(nextTile[0], nextTile[1], matrixTwo)
                                        openAdj = list()
                                        oepnAdj = self.openAdjacent(nextTile[0], nextTile[1], matrixTwo)

                                        #check for validbombLeft results
                                        if (result == 'valid'):
                                                bomb = bombLeft[1]
                                                if bomb > 0:
                                                        for adj in validAdj:
                                                                if adj not in listCoordinate:
                                                                        matrixTwo[adj[0]][adj[1]] = -1
                                                                        listValue.append(-1)
                                                                        listCoordinate.append((adj[0],adj[1]))
                                                elif bomb == 0:
                                                        for adj in validAdj:
                                                                if adj not in listCoordinate:
                                                                        matrixTwo[adj[0]][adj[1]] = -3
                                                                        listValue.append(-3)
                                                                        listCoordinate.append((adj[0],adj[1]))

                                        elif (result == 'invalid'):
                                                resu = False
                                                break
                                        elif (result == 'unknown'):
                                                for adj in validAdj:
                                                        if adj not in listCoordinate:
                                                                holeList.append((adj[0], adj[1]))
                                                                listValue.append('u')
                                                                listCoordinate.append((adj[0], adj[1]))

                        first = False
                        for extra in extraFirstTiles:
                                if (extra[0], extra[1]) not in listCoordinate:
                                        listCoordinate.append((extra[0], extra[1]))
                                        listValue.append(-2)

                        #check again to make sure
                        #to update any tiles that we weren't able to make an assumption previously.
                        #labeled as 'u' in the listValue, and its corresponding coordinates stored in holeList.
                        #we update them if possible.
                        #if there was even a single update, we repeat the process
                        if resu:
                                update = True

                                while update:
                                        update = False
                                        #updatePopQueue = deque()
                                        for tile in nextRunQueue:
                                                #check if the tile is a bomb, if so, move to the next tile
                                                if self.checkBoard(tile[0], tile[1], matrixTwo) != -1:
                                                        bombLeft = self.getBombLeft(tile[0], tile[1], matrixTwo)
                                                        result = self.validBombLeft(bombLeft)
                                                else:
                                                        continue
                                                validAdj = self.validAdjacent(tile[0], tile[1], matrixTwo)
                                                if (result == 'valid'):
                                                        bomb = bombLeft[1]
                                                        if bomb > 0:
                                                                for adj in validAdj:
                                                                        if (adj[0],adj[1]) in holeList:
                                                                                for index, item in enumerate(listCoordinate):
                                                                                        if item == adj:
                                                                                                listValue[index] = -1
                                                                                                matrixTwo[adj[0]][adj[1]] = -1
                                                                                                holeList.remove((adj[0],adj[1]))
                                                        elif bomb == 0:
                                                                for adj in validAdj:
                                                                        if (adj[0],adj[1]) in holeList:
                                                                                for index, item in enumerate(listCoordinate):
                                                                                        if item == adj:
                                                                                                listValue[index] = -3
                                                                                                matrixTwo[adj[0]][adj[1]] = -3
                                                                                                holeList.remove((adj[0],adj[1]))

                                                elif (result == 'invalid'):
                                                        resu = False
                                                        break

                                                #still not enough information, we skip.
                                                elif (result == 'unknown'):
                                                        continue


                                #check for the total remaining bomb
                                count = 0
                                if listValue:
                                        for l in listValue:
                                                if l == -1:
                                                        count += 1
                                if count > self.totalMines:
                                        resu = False

                        #start appending to dict collect
                        if resu:
                                tempDict = dict(zip(listCoordinate, listValue))
                                if not collect:
                                        collect = tempDict
                                else:
                                        for key, value in tempDict.items():
                                                if key not in collect:
                                                        collect[key] = value
                                                elif type(collect[key]) == list:
                                                        collect[key].append(value)
                                                else:
                                                        collect[key] = [collect[key],value]

                #end of for loop for assumption

                #key: coordinates
                #value: list of possible values for that coordinates in all the patterns, excluding the failed one.
                if collect:
                        for key, value in collect.items():

                                #if the value only has one assumption, it has type of int
                                #otherwise, it has type of set, which we can use len(set(value))
                                if isinstance(value, int):
                                        if value == -1:
                                                self.bombQueue.append(key)
                                        elif value == -3:
                                                self.safeQueue.append(key)
                                elif (len(set(value)) == 1):
                                        if list(set(value))[0] == -1:
                                                self.bombQueue.append(key)
                                        elif list(set(value))[0] == -3:
                                                self.safeQueue.append(key)
                                else:
                                        if theTile not in self.noAssumeList:
                                                self.noAssumeList.append(theTile)
