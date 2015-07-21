import pylab as plt
import pandas as pd
import numpy as np
from scipy import stats
import requests
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
import re
import random as ran
import time
import urllib2
from datetime import datetime
import string
import argparse
import sys
import json
import cPickle as pickle
import os.path


# gets the Dow Jones Industrial Average history from a downloaded csv (link in README)
# a next step would be to automate its download, which would require some form submission automation
def getDJIAHistoryCSV(pathToDJIACSV,allStratsRaw):
    indexHistory = pd.read_csv(pathToDJIACSV)
    indexHistory['DATE'] = pd.to_datetime(indexHistory['DATE']) # dates are parsed as objects in the frame, and need to be reparsed as datetimes
    indexHistory.columns = [u'Date', u'DJIA']
    indexHistory['DJIA'] = indexHistory['DJIA'].convert_objects(convert_numeric=True) # some of the value entries are blank, and we want NaNs
    indexHistory = indexHistory[np.isfinite(indexHistory['DJIA'])] # remove the NaN rows
    return indexHistory 


# gets the daily history for a chosen stock (by NYSE ticker) from Yahoo Finance
def getStockHistoryCSV(whichNYSE,allStratsRaw):
    page = requests.get('http://finance.yahoo.com/q/hp?s=' + whichNYSE + '+Historical+Prices')
    url = 'http://real-chart.finance.yahoo.com/table.' + page.text[page.text.find('csv'):page.text.rfind('csv')+3]
    stockHistory = pd.read_csv(url)
    # we currently don't do anything with this information, so we drop it.  Future versions will probably retain it though.
    stockHistory.drop([u'Open', u'High', u'Low', u'Close', u'Volume'], inplace=True, axis=1)
    stockHistory['Date'] = pd.to_datetime(stockHistory['Date']) # fix date issue as above
    stockHistory.columns = [u'Date', unicode(whichNYSE,"utf-8")]
    stockHistory = stockHistory.iloc[::-1] # reverse the rows in time, to bring them in line with what the algorithm does below
    return stockHistory 


# determines on what days the "Expert" strategy is updates, and what it wants to do
# this can be made far more interesting and sophisticated in the future
def getExpertStrategy(whichNYSE,allStratsRaw,addActions):

    # fix for the datetime conversion
    MonthConversion = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    # this, obnoxiously, has no field standard and needs to be manually updated every time a new one is encountered
    # a more clever and elegant way to hand new terms should be determined
    # in this case, something equivalent to a "Buy" translates to a 1, a "Neutral" translates to a 0.5, and a "Sell" translates to a 0
    ActionConversion = {'Buy':1, 'Underperform':0, 'Sector Perform':0.5, 'Neutral':0.5, 'Outperform':1, 'Mkt Underperform':0, 'Mkt Perform':0.5, 'Hold':0.5, 'Perform':0.5, 'Accumulate':1, 'Sell':0, 'In Line':0.5, 'Strong Buy':1, 'Overweight':1, 'Sector Outperform':1, 'Equal-weight':0.5, "Market Perform": 0.5, "NT Strong Buy":1, "NT Buy":1, "Attractive":1, "Mkt Outperform":1, "NT Neutral":0.5, "NT Accum":1, "LT Buy":1, "Reduce":0, "NT Accumulate":1, "Perform In Line":0.5, 'Average':0.5, 'Source of Funds':0, 'Above Average':1, 'Over Weight':1, 'Equal Weight':0.5, 'Peer Perform':0.5, 'Positive':1, 'In-Line':0.5, 'In-line':0.5, 'LT Neutral':0.5, 'Add':1, 'Maintain Position':0.5, 'NT Accum/LT Accum':1, 'Top Pick':1, 'Recomm. List':1, 'LT Attractive':1, 'Strong Sell':0, 'Underweight':0, 'Recomm List':1, 'Market Outperform':1, 'Perform-In-Line':0.5, 'Long-term Buy':1, 'Sector Underperform':0, '':0, 'Trading Buy':1, 'Outperf. Signif.':1, 'Recommended List':1, 'ST Neutral':0.5, 'Mkt Performer':0.5}

    expertWeights = []

    page = requests.get('http://finance.yahoo.com/q/ud?s=' + whichNYSE)

    # this way of parsing the text works well enough, but I think the split way above is more elegant and slightly faster
    lastRowInd = page.text.rindex('" nowrap>') + 9
    rowInd = page.text.index('" nowrap>') + 9
    while rowInd <= lastRowInd:    
        # get date
        dateCloseInd = page.text.index('</td>', rowInd)
        dateList = page.text[rowInd:dateCloseInd].split('-')
        dateList[1] = '-' + str(MonthConversion[dateList[1]])
        dateList[2] = '-' + str(dateList[2])
        date = pd.to_datetime(''.join(dateList), dayfirst=True)

        # get action weight (1 for buy, 0.5 for hold, 0 for sell)
        actionOpenInd = page.text.index('<b>', dateCloseInd) + 3
        actionClosedInd = page.text.index('</b>', actionOpenInd)
        actionKey = page.text[actionOpenInd:actionClosedInd]

        # makes sure to only crash if desired from CLI
        if addActions or actionKey in ActionConversion:
            action = ActionConversion[actionKey]
            expertWeights.append((date,action))

        if rowInd < lastRowInd:
            rowInd = page.text.index('" nowrap>', actionClosedInd) + 9
        else:
            break

    return expertWeights



# figure out what good and bad text is like (stupidly) using IMDB user reviews
def trainSentimentAnlaysis():
    reviewWords = getDictionaries('pos') + getDictionaries('neg')
    ran.shuffle(reviewWords) # this is only necessary if checking accuracy with cross-validation

    # see number of reviews for training
    print 'train on %d reviews' % (len(reviewWords))
    classifier = NaiveBayesClassifier.train(reviewWords)
    # interesting to see the most informative words and also to know that it's done
    classifier.show_most_informative_features()
    return classifier


# pretty straightforward way to make a list of the tuples of review word dictionary with the valence of the review
def getDictionaries(valence):
    if valence == 'pos':
        reviews = getReviews('http://www.imdb.com/chart/top?ref_=nv_ch_250_4')
    else:
        reviews = getReviews('http://www.imdb.com/chart/bottom')

    words =[(dict([(word, True) for word in review]),valence) for review in reviews]
    return words


# get the words out of the review
def getReviews(url):
    page = requests.get(url)
    pageProcessing = page.text.split('href="/title/') # the split trick for parsing allows for list comprehensions for grabbing the movies
    movies = [pageProcessing[2*i][:pageProcessing[2*i].index('/')] for i in xrange(1,101)]
    # grabs the movie reviews
    reviews = [getMovieReviews('http://www.imdb.com/title/' + movie + '/reviews?ref_=tt_ql_8') for movie in movies]
    # fixes the list of list of reviews for a specific movie into a list of all reviews for all movies
    combinedReviews = []
    for review in reviews:
        combinedReviews += review
    return combinedReviews


# parses the movie reviews
def getMovieReviews(url):
    print url # this is just to let you see your scraping progress thus far
    page = requests.get(url)
    pageProcessing = page.text.split('\n</div>\n<p>') # splitting trick for list comprehension again
    reviews = [re.findall(r"[\w']+",pageProcessing[i][:pageProcessing[i].index('</p>')]) for i in xrange(1,len(pageProcessing))]
    return reviews


# determines the NYT-Bot purchasing decision using IMDB classifier
def getNYTimesExpert(commonName,classifier,NYTimesApiKey):

    NYTExpert = []

    # get articles for years in the range of the Dow Jones csv (this should be automated in case year range changes)
    for year in xrange(2005,2016):

        # using the New York Times API to grab articles
        url = 'http://api.nytimes.com/svc/search/v2/articlesearch.json?q=stock+%22' + commonName.translate(string.maketrans(' ','+')) + '%22&begin_date=' + str(year) + '0101&end_date=' + str(year) + '1231&fl=pub_date,snippet,lead_paragraph,abstract,headline&api-key=' + NYTimesApiKey
        print repr(url)
        req = urllib2.Request(url, data=None, headers={'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        results = f.read()

        # since 10 articles are pulled per page by importance (meaning an ok spread across the year, focussing on major events if clustered)
        for whichArticle in xrange(10):
            # parse its json structure to get the publication date
            parsed_json = json.loads(results)
            date_posted = parsed_json['response']['docs'][whichArticle]['pub_date']
            date_posted = datetime.strptime(date_posted, '%Y-%m-%dT%H:%M:%SZ')

            # parse the json to get just the string for an individual article, which is then split into a word dictionary for 
            # "Buy" or "Sell" determination by classifier
            words = re.findall(r"[\w']+",json.dumps(parsed_json['response']['docs'][whichArticle]))
            articleDict = dict([(word, True) for word in words])
            valence = classifier.classify(articleDict)
            if valence == 'pos':
                NYTExpert.append((date_posted,1)) # "Buy"
            else:
                NYTExpert.append((date_posted,0)) # "Sell"

    # since returns are by importance and not date, sort everything the correct way for condensing
    NYTExpert = sorted(NYTExpert, key=lambda tup: tup[0], reverse=True)
    return NYTExpert


# this fleshes out the time series of the portfolio using the purchasing decisions of both the bot and the experts
# there is a for loop in here that needs to be dealt with because it is way-way to slow
def fillExpert(condensedData,whichNYSE,expertWeights,whichExpert):
    
    expertMoney = [] # will become a list of money at increasing dates
    whichWeight = len(expertWeights) - 1 # because of the temporal ordering on expert opinion, first date is the last element
    amountDJIA = 1.0    # the safest default strategy is to be all index
    amountNYSE = 0.0
    # total portfolio is the sum of the stocks and index
    # this calculation and setup is relatively inflexible and should be modified for multiple stocks strategies
    expertMoney.append(amountDJIA + amountNYSE)

    # this is now fast enough
    for row in xrange(1,len(condensedData['Date'])):

        # redistribute investment based on expert opinion
        if whichWeight >= 0 and condensedData['Date'][row] >= expertWeights[whichWeight-1][0]: # there is a new date with a strategy now
            whichWeight -= 1
            # "Buy" means put all money in the stock
            if expertWeights[whichWeight][1] == 1:
                amountNYSE += amountDJIA
                amountDJIA = 0
            # "Sell" means put all money in the index
            elif expertWeights[whichWeight][1] == 0:
                amountDJIA += amountNYSE
                amountNYSE = 0
            # "Hold" means split money between stock and index
            else:
                amountNYSE = (amountNYSE+amountDJIA)/2
                amountDJIA = amountNYSE

        # update the amounts day over day for the index and stock
        amountNYSE *= condensedData[whichNYSE][row] / condensedData[whichNYSE][row-1]
        amountDJIA *= condensedData['DJIA'][row] / condensedData['DJIA'][row-1]

        # check progress
        #print whichExpert + ':  ' + str(condensedData['Date'][row]) + '     ' + str(amountDJIA) + '     ' + str(amountNYSE)
        # maybe don't update table here
        expertMoney.append(amountNYSE + amountDJIA)

    return expertMoney


# takes the expertly determined weights for given dates for both "Experts" and "NYT-Bot and appends them to the stock DataFrame
def condenseStrategyData(allStratsRaw,whichNYSE,expertWeights):
    keys = list(allStratsRaw.keys())

    # doing this before the expert models below is key for restricting dates to only those with useful data
    condensedData = allStratsRaw[keys.pop()]
    # already set up for multiple stocks, they just need to be implemented at the main program level
    while len(keys) > 0:
        toJoinData = allStratsRaw[keys.pop()]
        condensedData = pd.merge(condensedData, toJoinData, how='inner', on='Date')
    # this series of steps for adding the expert models is too slow for reasons mentioned in the fillExpert function
    condensedData['Expert'] = pd.Series(fillExpert(condensedData,whichNYSE,expertWeights['Expert'],'Expert'), index=condensedData.index)
    condensedData['NYT-Bot'] = pd.Series(fillExpert(condensedData,whichNYSE,expertWeights['NYT-Bot'],'NYT-Bot'), index=condensedData.index)

    # this step is necessary for the plotting feature for dataframes to work as desired
    condensedData = condensedData.set_index(u'Date')
    return condensedData


# make the pretty graphs
def plotCorrelations(condensedData):
    keys = list(condensedData.columns)
    # start all strategies at 1 to see their relative change in revenue
    for key in keys:
        condensedData[key] = condensedData[key] / condensedData[key][0]
    condensedData.plot()
    plt.xlabel('Date')
    plt.ylabel('Money')
    plt.show()


# run the Bot
def NLPBot(whichNYSE,commonName,NYTimesApiKey,update,addActions):

    if update == 'True':
        allStratsRaw = None
        classifier = None
        expertWeights = None
        condensedData = None
    else:
        if os.path.isfile('allStratsRaw.p'):
            allStratsRaw = pickle.load(open("allStratsRaw.p", "rb"))
        else:
            allStratsRaw = None
        if os.path.isfile('classifier.p'):
            classifier = pickle.load(open("classifier.p", "rb"))
        else:
            classifier = None
        if os.path.isfile('expertWeights.p'):
            expertWeights = pickle.load(open("expertWeights.p", "rb"))
        else:
            expertWeights = None
        if os.path.isfile('condensedData.p'):
            condensedData = pickle.load(open("condensedData.p", "rb")) 
        else:
            condensedData = None
   
    if not isinstance(allStratsRaw, dict) or not 'DJIA' in allStratsRaw:
        allStratsRaw = {}
        pathToDJIACSV = 'DJIA.csv'
        allStratsRaw['DJIA'] = getDJIAHistoryCSV(pathToDJIACSV,allStratsRaw)
        pickle.dump(allStratsRaw, open("allStratsRaw.p", "wb"))

    if not whichNYSE in allStratsRaw:
        allStratsRaw[whichNYSE] = getStockHistoryCSV(whichNYSE,allStratsRaw)
        pickle.dump(allStratsRaw, open("allStratsRaw.p", "wb"))
  
    if not isinstance(expertWeights, dict) or not 'Expert' in expertWeights:
        expertWeights = {}
        expertWeights['Expert'] = getExpertStrategy(whichNYSE,allStratsRaw,addActions=='True')   
        pickle.dump(expertWeights, open("expertWeights.p", "wb"))

    if not 'NYT-Bot' in expertWeights:
        if classifier == None:
            classifier = trainSentimentAnlaysis()
            pickle.dump(classifier, open("classifier.p", "wb"))
        expertWeights['NYT-Bot'] = getNYTimesExpert(commonName,classifier,NYTimesApiKey)
        pickle.dump(expertWeights, open("expertWeights.p", "wb"))

    if not isinstance(condensedData, pd.DataFrame) or not whichNYSE in condensedData:
        condensedData = condenseStrategyData(allStratsRaw,whichNYSE,expertWeights)
        pickle.dump(condensedData, open("condensedData.p", "wb"))

    plotCorrelations(condensedData)


if __name__ == '__main__':

    if len(sys.argv) != 7:
        print "\n" \
            "Your number of arguments is " + str(len(sys.argv)-2) + "\n" \
            "\n" \
            "The correct usage of NYT-Bot is as follows:\n" \
            "\n" \
            "python NLPBot.py NLPBot [arg1] [arg2] [arg3] [arg4]\n" \
            "\n" \
            "arg1 - what is the NYSE ticker label for the company you want to model, e.g. AAPL for Apple\n" \
            "\n" \
            "arg2 - what is the common name for the company, e.g. Bank\ of\ America for Bank of America\n" \
            "       WARNING: you MUST escape spaces in the company name, i.e. a \" \" should be \"\\ \"\n" \
            "\n" \
            "arg3 - what is your New York Times Article API V2 key\n" \
            "\n" \
            "arg4 - True or False : do you want to redownload and recalculate values for everything already saved from previous runs?\n" \
            "\n" \
            "arg5 - True or False : do you want to have crashes on unexpected Expert Actions so that you can manually edit/update the dictionary in this program?\n" \
            "\n"
    else:
        function_map = { 
            'NLPBot': NLPBot
        }
        parser = argparse.ArgumentParser()
        parser.add_argument('command')
        parser.add_argument('whichNYSE')
        parser.add_argument('commonName')
        parser.add_argument('NYTimesApiKey')
        parser.add_argument('update')
        parser.add_argument('addActions')
        args = parser.parse_args()
        function = function_map[args.command]
        function(args.whichNYSE, args.commonName, args.NYTimesApiKey, args.update, args.addActions)
