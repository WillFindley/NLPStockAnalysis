# A Natural Language Processing, Stock Buying Emulation Bot

Based on sentiment analysis training from IMDB to classify New York Times articles about companies

## Installation

download the DJIA.csv file [from here](https://research.stlouisfed.org/fred2/series/DJIA/downloaddata)

download my NLPBot.py file

get a New York Times Articles API V2 key [from here](http://developer.nytimes.com/docs/read/article_search_api_v2)

## Usage

The correct usage of NYT-Bot is as follows:

python NLPBot.py NLPBot [arg1] [arg2] [arg3] [arg4] [arg5]

arg1 - what is the NYSE ticker label for the company you want to model, e.g. AAPL for Apple

arg2 - what is the common name for the company, e.g. Bank\ of\ America for Bank of America
       WARNING: you MUST escape spaces in the company name, i.e. a " " should be "\ "

arg3 - what is your New York Times Article API V2 key

arg4 - True or False : do you want to redownload and recalculate values for everything already saved from previous runs?

arg5 - True or False : do you want to have crashes on unexpected Expert Actions so that you can manually edit/update the dictionary in this program?


## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

Alpha version 0.0001 on 06/26/2015

## Credits

Will Findley
