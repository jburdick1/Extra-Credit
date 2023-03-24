import nltk
from newsapi import NewsApiClient
from newspaper import Article
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# initialize NLTK's Vader module
nltk.download('vader_lexicon')

# initialize NewsApiClient with your API key
api_key = 'a81a2f3a42104f77aa29a2cdd60a0623'
newsapi = NewsApiClient(api_key=api_key)

# set query parameters
query = 'markets'
sources = 'bbc-news,the-verge'
language = 'en'

# get the latest articles related to CPI
articles = newsapi.get_everything(q=query, sources=sources, language=language)

# retrieve the URL of the first article in the response
url = articles['articles'][0]['url']

# create an Article object and download the article content
article = Article(url)
article.download()

# parse the article content and extract the main text
article.parse()
text = article.text

# perform sentiment analysis on the article text
analyzer = SentimentIntensityAnalyzer()
score = analyzer.polarity_scores(text)

# print the sentiment scores
print(score)



#Need to make this a function still so i can call it with various search terms
# maybe make a compound score of the sentiments 
# maybe change the news source to wsj
# find better search terms