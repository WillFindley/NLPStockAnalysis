import pylab as plot
import pandas as pd
import numpy as np
import requests

def getStockHistoryCSV(whichNYSE):
    page = requests.get('http://finance.yahoo.com/q/hp?s=' + whichNYSE + '+Historical+Prices')
    url = 'http://real-chart.finance.yahoo.com/table.' + page.text[page.text.find('csv'):page.text.rfind('csv')+3]
    stockHistory = pd.read_csv(url)
    stockHistory['Date'] = pd.to_datetime(stockHistory['Date'])
    return stockHistory


def plotCorrelations(stockHistory):
    x = stockHistory['Date'][0:-1]
    y = (stockHistory['Adj Close'][0:-1] - stockHistory['Adj Close'][1:]) / stockHistory['Adj Close'][1:]
    plot(x,y)
    xlabel('Date')
    ylabel('% Change Close-To-Close')
    plot.show()
