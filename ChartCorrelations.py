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
    page = requests.get('http://finance.yahoo.com/q/ud?s=' + whichNYSE)
    lastRowInd = page.text.rindex('" nowrap>')
    rowInd = page.text.index('" nowrap>')
    while rowInd <= lastRowInd:    


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
