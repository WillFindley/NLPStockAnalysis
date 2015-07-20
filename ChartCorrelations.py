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


def getDJIAHistoryCSV(pathToDJIACSV,allStratsRaw):
    indexHistory = pd.read_csv(pathToDJIACSV)
    indexHistory['DATE'] = pd.to_datetime(indexHistory['DATE'])
    indexHistory.columns = [u'Date', u'DJIA']
    indexHistory['DJIA'] = indexHistory['DJIA'].convert_objects(convert_numeric=True)
    indexHistory = indexHistory[np.isfinite(indexHistory['DJIA'])]
    allStratsRaw['DJIA'] = indexHistory
    return allStratsRaw


def getStockHistoryCSV(whichNYSE,allStratsRaw):
    page = requests.get('http://finance.yahoo.com/q/hp?s=' + whichNYSE + '+Historical+Prices')
    url = 'http://real-chart.finance.yahoo.com/table.' + page.text[page.text.find('csv'):page.text.rfind('csv')+3]
    stockHistory = pd.read_csv(url)
    stockHistory.drop([u'Open', u'High', u'Low', u'Close', u'Volume'], inplace=True, axis=1)
    stockHistory['Date'] = pd.to_datetime(stockHistory['Date'])
    stockHistory.columns = [u'Date', unicode(whichNYSE,"utf-8")]
    stockHistory = stockHistory.iloc[::-1]
    allStratsRaw[whichNYSE] = stockHistory
    return allStratsRaw


def getExpertStrategy(whichNYSE,allStratsRaw):

    MonthConversion = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    ActionConversion = {'Buy':1, 'Underperform':0, 'Sector Perform':0.5, 'Neutral':0.5, 'Outperform':1, 'Mkt Underperform':0, 'Mkt Perform':0.5, 'Hold':0.5, 'Perform':0.5, 'Accumulate':1, 'Sell':0, 'In Line':0.5, 'Strong Buy':1, 'Overweight':1, 'Sector Outperform':1, 'Equal-weight':0.5, "Market Perform": 0.5, "NT Strong Buy":1, "NT Buy":1, "Attractive":1, "Mkt Outperform":1, "NT Neutral":0.5, "NT Accum":1, "LT Buy":1, "Reduce":0, "NT Accumulate":1, "Perform In Line":0.5, 'Average':0.5, 'Source of Funds':0, 'Above Average':1, 'Over Weight':1, 'Equal Weight':0.5, 'Peer Perform':0.5, 'Positive':1, 'In-Line':0.5, 'In-line':0.5, 'LT Neutral':0.5, 'Add':1, 'Maintain Position':0.5, 'NT Accum/LT Accum':1, 'Top Pick':1, 'Recomm. List':1, 'LT Attractive':1}

    expertWeights = []

    page = requests.get('http://finance.yahoo.com/q/ud?s=' + whichNYSE)
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
        action = ActionConversion[page.text[actionOpenInd:actionClosedInd]]

        expertWeights.append((date,action))

        if rowInd < lastRowInd:
            rowInd = page.text.index('" nowrap>', actionClosedInd) + 9
        else:
            break

    return expertWeights


def condenseStrategyData(allStratsRaw,whichNYSE,expertWeights):
    keys = list(allStratsRaw.keys())
    condensedData = allStratsRaw[keys.pop()]
    while len(keys) > 0:
        toJoinData = allStratsRaw[keys.pop()]
        condensedData = pd.merge(condensedData, toJoinData, how='inner', on='Date')
    condensedData['Expert'] = pd.Series(np.random.randn(len(condensedData['Date'])), index=condensedData.index)
    condensedData['NYT-Bot'] = pd.Series(np.random.randn(len(condensedData['Date'])), index=condensedData.index)
    condensedData = fillExpert(condensedData,whichNYSE,expertWeights['Expert'],'Expert')
    condensedData = fillExpert(condensedData,whichNYSE,expertWeights['NYT-Bot'],'NYT-Bot')
    condensedData = condensedData.set_index(u'Date')
    return condensedData


def fillExpert(condensedData,whichNYSE,expertWeights,whichExpert):
   
    whichWeight = len(expertWeights) - 1
    amountDJIA = 1.0
    amountNYSE = 0.0
    condensedData[whichExpert][0] = amountDJIA + amountNYSE
    for row in xrange(1,len(condensedData[whichExpert])):

        # redistribute investment based on expert opinion
        if whichWeight >= 0 and condensedData['Date'][row] >= expertWeights[whichWeight-1][0]:
            whichWeight -= 1
            if expertWeights[whichWeight][1] == 1:
                amountNYSE += amountDJIA
                amountDJIA = 0
            elif expertWeights[whichWeight][1] == 0:
                amountDJIA += amountNYSE
                amountNYSE = 0
            else:
                amountNYSE = (amountNYSE+amountDJIA)/2
                amountDJIA = amountNYSE

        amountNYSE *= condensedData[whichNYSE][row] / condensedData[whichNYSE][row-1]
        amountDJIA *= condensedData['DJIA'][row] / condensedData['DJIA'][row-1]
        
        print whichExpert + ':  ' + str(condensedData['Date'][row]) + '     ' + str(amountDJIA) + '     ' + str(amountNYSE)
        condensedData[whichExpert][row] = amountNYSE + amountDJIA

    return condensedData


def trainSentimentAnlaysis():
    reviewWords = getDictionaries('pos') + getDictionaries('neg')
    ran.shuffle(reviewWords)

    print 'train on %d reviews' % (len(reviewWords))
    classifier = NaiveBayesClassifier.train(reviewWords)
    classifier.show_most_informative_features()
    return classifier


def getDictionaries(valence):
    if valence == 'pos':
        reviews = getReviews('http://www.imdb.com/chart/top?ref_=nv_ch_250_4')
    else:
        reviews = getReviews('http://www.imdb.com/chart/bottom')

    words =[(dict([(word, True) for word in review]),valence) for review in reviews]
    return words


def getReviews(url):
    page = requests.get(url)
    pageProcessing = page.text.split('href="/title/')
    movies = [pageProcessing[2*i][:pageProcessing[2*i].index('/')] for i in xrange(1,101)]
    reviews = [getMovieReviews('http://www.imdb.com/title/' + movie + '/reviews?ref_=tt_ql_8') for movie in movies]
    combinedReviews = []
    for review in reviews:
        combinedReviews += review
    return combinedReviews


def getMovieReviews(url):
    print url
    page = requests.get(url)
    pageProcessing = page.text.split('\n</div>\n<p>')
    reviews = [re.findall(r"[\w']+",pageProcessing[i][:pageProcessing[i].index('</p>')]) for i in xrange(1,len(pageProcessing))]
    return reviews


def getNYTimesExpert(commonName,classifier):

    NYTExpert = []

    for year in xrange(2005,2016):

        url = 'http://api.nytimes.com/svc/search/v2/articlesearch.json?q=stock+%22' + commonName.translate(string.maketrans(' ','+')) + '%22&begin_date=' + str(year) + '0101&end_date=' + str(year) + '1231&fl=pub_date,snippet,lead_paragraph,abstract,headline&api-key=190420596a5dfacbbb17f03f4030eb5e:14:63405689'
        req = urllib2.Request(url, data=None, headers={'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        results = f.read()

        for whichArticle in xrange(10):
            parsed_json = json.loads(results)
            date_posted = parsed_json['response']['docs'][whichArticle]['pub_date']
            date_posted = datetime.strptime(date_posted, '%Y-%m-%dT%H:%M:%SZ')

            words = re.findall(r"[\w']+",json.dumps(parsed_json['response']['docs'][whichArticle]))
            articleDict = dict([(word, True) for word in words])
            valence = classifier.classify(articleDict)
            if valence == 'pos':
                NYTExpert.append((date_posted,1))
            else:
                NYTExpert.append((date_posted,0))
        
    NYTExpert = sorted(NYTExpert, key=lambda tup: tup[0], reverse=True)
    return NYTExpert


def plotCorrelations(condensedData):
    keys = list(condensedData.columns)
    # start all strategies at $1
    for key in keys:
        condensedData[key] = condensedData[key] / condensedData[key][0]
    condensedData.plot()
    plt.xlabel('Date')
    plt.ylabel('Money')
    plt.show()


allStratsRaw = {}
expertWeights = {}
pathToDJIACSV = 'DJIA.csv'
allStratsRaw = getDJIAHistoryCSV(pathToDJIACSV,allStratsRaw)
commonName = 'Apple'
whichNYSE = 'AAPL'
allStratsRaw = getStockHistoryCSV(whichNYSE,allStratsRaw)
expertWeights['Expert'] = getExpertStrategy(whichNYSE,allStratsRaw)
#classifier = trainSentimentAnlaysis()
expertWeights['NYT-Bot'] = getNYTimesExpert(commonName,classifier)
condensedData = condenseStrategyData(allStratsRaw,whichNYSE,expertWeights)
plotCorrelations(condensedData)
