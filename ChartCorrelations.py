import pylab as plt
import pandas as pd
import numpy as np
from scipy import stats
import requests


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
    allStratsRaw[whichNYSE] = stockHistory
    return allStratsRaw


def getExpertStrategy(whichNYSE,allStratsRaw):

    MonthConversion = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    ActionConversion = {'Buy':1, 'Underperform':0, 'Sector Perform':0.5, 'Neutral':0.5, 'Outperform':1, 'Mkt Underperform':0, 'Mkt Perform':0.5, 'Hold':0.5, 'Perform':0.5, 'Accumulate':1, 'Sell':0, 'In Line':0.5, 'Strong Buy':1, 'Overweight':1, 'Sector Outperform':1, 'Equal-weight':0.5, "Market Perform": 0.5, "NT Strong Buy":1, "NT Buy":1, "Attractive":1, "Mkt Outperform":1, "NT Neutral":0.5, "NT Accum":1, "LT Buy":1, "Reduce":0, "NT Accumulate":1, "Perform In Line":0.5}

    expertWeights = []

    page = requests.get('http://finance.yahoo.com/q/ud?s=' + whichNYSE)
    lastRowInd = page.text.rindex('" nowrap>') + 9
    rowInd = page.text.index('" nowrap>') + 9
    while rowInd <= lastRowInd:    
        
        # get date
        dateCloseInd = page.text.index('</td>', rowInd)
        dateList = page.text[rowInd,dateCloseInd].split('-')
        dateList[1] = '-' + MonthConversion[dateList[1]]
        dateList[2] = '-' + dateList[2]
        date = pd.to_datetime(''.join(dateList), dayfirst=True)

        # get action weight (1 for buy, 0.5 for hold, 0 for sell)
        actionOpenInd = page.text.index('<b>', dateCloseInd) + 3
        actionClosedInd = page.text.index('</b>', actionOpenInd)
        action = ActionConversion[page.text[actionOpenInd,actionClosedInd]]

        expertWeights.append((date,action))

        if rowInd < lastRowInd:
            rowInd = page.text.index('" nowrap>', actionClosedInd) + 9

    return expertWeights


def condenseStrategyData(allStratsRaw):
    keys = list(allStratsRaw.keys())
    condensedData = allStratsRaw[keys.pop()]
    while len(keys) > 0:
        toJoinData = allStratsRaw[keys.pop()]
        condensedData = pd.merge(condensedData, toJoinData, how='inner', on='Date')
    condensedData = condensedData.set_index(u'Date')
    return condensedData


def plotCorrelations(condensedData):
    keys = list(condensedData.columns)
    # start all strategies at $1
    for key in keys:
        condensedData[key] = condensedData[key] / condensedData[key][-1]
    condensedData.plot()
    plt.xlabel('Date')
    plt.ylabel('Money')
    plt.show()


#allStratsRaw = {}
#pathToDJIACSV = 'DJIA.csv'
#allStratsRaw = getDJIAHistoryCSV(pathToDJIACSV,allStratsRaw)
whichNYSE = 'BAC'
#allStratsRaw = getStockHistoryCSV(whichNYSE,allStratsRaw)
condensedData = condenseStrategyData(allStratsRaw)
plotCorrelations(condensedData)
