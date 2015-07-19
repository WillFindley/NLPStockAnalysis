import numpy as np
import copy

def runQ1():

    Ns = [8,16,32]
    for N in Ns:

        subChainAnswers = {}    # computed answers for subchains 
        # start the recursion
        probabilityDistribution = np.array(recursiveDP(copy.deepcopy(['w'+(N-2)*'b'+'w']),subChainAnswers,0))
        mean = np.dot(probabilityDistribution[:,0],probabilityDistribution[:,1]/np.float64(sum(probabilityDistribution[:,1])))
        std = np.sqrt(np.dot((probabilityDistribution[:,0]-mean)**2,probabilityDistribution[:,1]/np.float64(sum(probabilityDistribution[:,1]))))
        print 'For N = ' + str(N) + ', the mean = ' + str(mean) + ' and the standard deviation = ' + str(std)


def recursiveDP(remainingChain,subChainAnswers,deltaNumChains):

    deltaNumChains = min(0,deltaNumChains) #prep to add in a split to number of chains

    remainingChain.sort()
    # woo-hoo dynamic programming
    key = ''.join([subchain+'s' for subchain in remainingChain])
    if subChainAnswers.has_key(key):
        answer = copy.deepcopy(subChainAnswers[key])
        return deltaNCCorrection(answer,deltaNumChains)

    # base case where removing anything doesn't change the answer
    if key == 'ws':
        subChainAnswers[key] = [[1,1]]
        return copy.deepcopy(subChainAnswers[key])

    answerPDF = []
    for whichSubChain in xrange(len(remainingChain)):
        listSubChain = list(remainingChain[whichSubChain])
        for whichLink in xrange(len(listSubChain)):
            # copying the objects so they can get changed without ruining further loop iterations
            newRemainingChain = copy.deepcopy(remainingChain)
            newRemainingChain.pop(whichSubChain)
            tmpChain = copy.deepcopy(listSubChain)
            
            if len(tmpChain) == 1:
                deltaNumChains -= 1 
                # if splitting here, so need to add 1 to subanswers
                # if a subchain is removed, need to subtract 1 from subanswers
                answerPDF.append(addChainSplit(recursiveDP(newRemainingChain,subChainAnswers,deltaNumChains),deltaNumChains))
                deltaNumChains += 1
            elif whichLink == 0 or whichLink == len(tmpChain)-1:
                tmpChain.pop(0)
                tmpChain[0] = 'w'
                newRemainingChain.insert(whichSubChain,''.join(tmpChain))
                key = ''.join([subchain+'s' for subchain in newRemainingChain])
                newRemainingChain = key.split('s')
                newRemainingChain.pop(-1)
                # if splitting here, so need to add 1 to subanswers
                # if a subchain is removed, need to subtract 1 from subanswers
                answerPDF.append(addChainSplit(recursiveDP(newRemainingChain,subChainAnswers,deltaNumChains),deltaNumChains))
            else:
                deltaNumChains += 1
                tmpChain[whichLink] = 's'
                tmpChain[whichLink-1] = 'w'
                tmpChain[whichLink+1] = 'w'
                newRemainingChain.insert(whichSubChain,''.join(tmpChain))
                key = ''.join([subchain+'s' for subchain in newRemainingChain])
                newRemainingChain = key.split('s')
                newRemainingChain.pop(-1)
                # if splitting here, so need to add 1 to subanswers
                # if a subchain is removed, need to subtract 1 from subanswers
                answerPDF.append(addChainSplit(recursiveDP(newRemainingChain,subChainAnswers,deltaNumChains),deltaNumChains))
                deltaNumChains -= 1
    # need to condense and combine all of the subanswers, in addition to correcting for odds for each
    key = ''.join([subchain+'s' for subchain in remainingChain])
    subChainAnswers[key] = mergeSubAnswers(answerPDF)
    return copy.deepcopy(subChainAnswers[key])


def deltaNCCorrection(answer,deltaNumChains):

    answer = [[[max(1,subAnswer[0]+deltaNumChains),subAnswer[1]] for subAnswer in answer]]
    return mergeSubAnswers(answer)


def addChainSplit(oldAnswer,deltaNumChains):
    
    if deltaNumChains == 1:
        # adds 1 to all of the subchain numbers because there's a new split
        return [[numChains[0]+deltaNumChains,numChains[1]] for numChains in oldAnswer]
    else:
        return oldAnswer


def mergeSubAnswers(answerPDF):
    
    newAnswers = [] # store the merged answers in here
    maxLength = 1   # start off looking for max number of chains of 1
    while len(answerPDF) > 0:   # keep checking while there are still answers left to merge
        
        tmpAnswer = [maxLength,0]   # initialize to 0 for the number of any chain number
       
        i = 0
        while i < len(answerPDF):
            # continue the loop and pull out sub-answers, so long as they exist
            whichAnswer = answerPDF.pop(i)

            j = 0
            while j < len(whichAnswer):
               
                # look at the individual merged solutions in the subanswers and pull out the ones of the correct chain number
                if whichAnswer[j][0] == maxLength:
                    tmpAnswer[1] += whichAnswer.pop(j)[1]   # update the merged tally of this number of chains
                    # do not update j for the while loop since the length decreased by 1 (the popped element)
                else:
                    # since answer did not have this number of chains, update to look at the next answer
                    j += 1
            
            if whichAnswer != []:
                # if there is something left in this subanswer's set of answers, add it back into the list and update the index to the next subanswer.  Otherwise just leave it out and don't update
                answerPDF.insert(i,whichAnswer)
                i += 1
        
        # add my merged findings for the number of chains, and check the next higher number
        newAnswers.append(tmpAnswer)
        maxLength += 1
    return newAnswers


runQ1()
