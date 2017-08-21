# -*- coding: utf-8 -*-

from urllib.request import urlopen
from pymongo import MongoClient
import json
import configparser
import logging  
import logging.config
import time
import re

# get ready for logging
logging.config.fileConfig('log.cfg')  
logger = logging.getLogger('root')
logger.info('Data Collection Program started to work') 

# connect to MongoDB
client = MongoClient('localhost', 27017)
# Database Name: tweets_db
db = client['tweets_db']
logger.info('Connected to MongoDB successfully') 

# read from config file
cfg = configparser.ConfigParser()
cfg.read('news.cfg')
cfg.sections()

# secret key for News API
API_KEY = cfg['NEWS_ACCESS']['API_KEY']
# URL for the news agency list 
ACCESS_URL_AGENCY = 'https://newsapi.org/v1/sources?language=en&apiKey=' + API_KEY 
# URL for the news article list that each news agency offers
ACCESS_URL_ARTICLE = 'https://newsapi.org/v1/articles?source={0}&sortBy={1}&apiKey=' + API_KEY

# stopwords
STOP_WORDS = cfg['NLTK']['STOP_WORDS']
# stop words list
STOP_WORDS = [x.strip() for x in STOP_WORDS.split(',')]
# agency list
agencyIdList = [ x.strip() for x in cfg['PARSE_LIST']['AGENCY_ID'].split(',')]
# country id/name dictionary
COUNTRY = dict(cfg['COUNTRY'].items())

# ---------------------------------------------------
# Get a list of all News Agencies that News API offers
# ---------------------------------------------------
def getAgencies(): 
    # access the URL
    resp = urlopen(ACCESS_URL_AGENCY)
    # read the JSON-format outcome
    jsn = json.loads(resp.read().decode('utf8'))
    for agency in jsn['sources']:
        # get the sort type that how the news agency orders their news articles
        sortTypes = agency['sortBysAvailable']
        # latest articles as the priority for selection
        if 'latest' in sortTypes:
            sort = 'latest'
        else:
            # or take the first option
            sort = sortTypes[0]
        # record the log
        logger.info('Deal with agency [{0}] - start'.format(agency['id']))
        # get the news articles from each News Agency
        getArticles(agency['id'], agency['name'], sort, agency['category'], agency['country'])
        logger.info('Deal with agency [{0}] - end'.format(agency['id']))
        logger.info('Sleep for 60s')
        logger.info('-' * 50)
        # sleep for 60 seconds
        time.sleep(60)

# ---------------------------------------------------
# Get all the news articles (general info) from each News Agency
# ---------------------------------------------------
def getArticles(agencyId, agencyName, sort, category, country):
    # generate a News API URL for a specific news agency
    newsList_url = ACCESS_URL_ARTICLE.format(agencyId, sort)
    logger.info('News List - {0}'.format(newsList_url))
    # visit the URL
    resp = urlopen(newsList_url)
    # read the JSON-format outcome
    jsn = json.loads(resp.read().decode('utf8'))
    # insert news articles information into collection NEWS
    for news in jsn['articles']:
        insertToTab(agencyId, agencyName, news['author'], news['title'], news['description'], news['url'], news['urlToImage'], news['publishedAt'], category, country)
 
# ---------------------------------------------------
# Insert news articles (general information) into collection NEWS
# ---------------------------------------------------        
def insertToTab(agencyId, agencyName, author, title, description, url, urlToImage, publishedAt, category, country):
    # if the article exists already (has same URL or same title)
    if None != db.news.find_one({ '$or': [ {'url': url}, {'title': title} ] }):
        logger.info('Article has already existed - ' + url)
        return
     
    # do not take any news article with empty title
    if title is None or title is '' or title.strip() is '':
        logger.info('Title is empty - ' + url)
        return

    # do not take any news article with empty description
    if description is None or description is '' or description.strip() is '':
        logger.info('Description is empty - ' + url)
        return        

    # do not take any news article with empty published date
    if publishedAt is None or publishedAt is '' or publishedAt.strip() is '':
        publishedAt = time.strftime("%Y-%m-%d", time.localtime())
        logger.info('PublishedAt is empty - fill with current date' + url)
        return    
    
    # generate keywords from a news' description
    keywords = getKeywords(description)
    if not keywords:
        logger.info('Keywords from description is empty - ' + url)
        return 

    entity = {'agencyId': agencyId,
              'agencyName': agencyName,
              'author': author,
              'title': title,
              'description': description,
              'keywords': keywords,
              'countryId': country,
              'countryName': COUNTRY[country],
              'url': url,
              'urlToImage': urlToImage,
              'publishedAt': publishedAt,
              'category': category}
    try:
        # insert into the collection NEWS
        db.news.insert_one(entity)  
        logger.info('Write into DB - DONE')
    except Exception as e:
        logger.error('Write into DB - FAILED')
        logger.error(e)

# ---------------------------------------------------
# Gernerate keywords list from description
# ---------------------------------------------------
def getKeywords(sentence):
    if (None == sentence or '' == sentence.strip()):
        return ''
    
    # standardization
    sen = sentence.lower()
    # remove sentence symbols
    sen = re.sub(r'''[,|;|.|"|?]''', ' ', sen)
    # for [He's I'm We're Tom's]
    sen = re.sub(r"'s |'re |'m ", ' ', sen)
    # split sentence into words (remove stop words and sentence symbols)
    keywords = [ w for w in sen.split() if w not in STOP_WORDS]
    # remove duplicated words, and MongoDB accepts LIST only
    return list(set(keywords)) 
    
if __name__=="__main__":
    # start and keep running
    while True:
        getAgencies()