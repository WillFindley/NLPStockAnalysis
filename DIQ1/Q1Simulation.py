import math
import numpy as np
from random import shuffle

def simulateChainProblem():

    nValues = [32]
    for N in nValues:
        answer = runSimulation(N)
        print answer


def runSimulation(N):

    simulatedAnswers = []
    currentTolerance = 1;
    # keep simulating the chain problem until the answers are precisely enough known
    while True:

        # initialize the new and old chain
        oldChain = [number for number in xrange(N)]
        shuffle(oldChain)   # shuffle the oldChain to pull links out at random
        newChain = []

        # simulate the chain formation and max number of subchains
        maxNumChains = 1
        while len(oldChain) > 0:
            newChain = addToNewChain(newChain,oldChain.pop())
            maxNumChains = max(maxNumChains,len(newChain))
        simulatedAnswers.append(np.float64(maxNumChains)) 
       
        if len(simulatedAnswers) > 1:
            print str(round(np.std(simulatedAnswers,dtype=np.float64),9)) + '     ' + str(round(np.mean(simulatedAnswers,dtype=np.float64),9))


def addToNewChain(newChain,link):

    for whichSubChain in xrange(len(newChain)):
        # if the prior link is already there
        if newChain[whichSubChain][len(newChain[whichSubChain])-1] == link-1:
            newChain[whichSubChain].append(link)
            # if the following link is already there too, but only if it's not the last link already
            if whichSubChain+1 != len(newChain) and newChain[whichSubChain+1][0] == link+1:
                # remove the subChain that should now be connected by the link to the previous subchain, and connect them
                newChain[whichSubChain].extend(newChain.pop(whichSubChain+1))
            return newChain
        # if only the following link is there
        elif newChain[whichSubChain][0] == link+1:
            newChain[whichSubChain].insert(0,link)
            return newChain
        # if subchains are already further in the original chain, go ahead and insert it here
        elif newChain[whichSubChain][0] > link:
            newChain.insert(whichSubChain,[link])
            return newChain
    # insert it in the correct spot if it is its own subchain, since it couldn't connect to anything
    newChain.append([link])
    return newChain

simulateChainProblem()
