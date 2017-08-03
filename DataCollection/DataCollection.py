# -*- coding: utf-8 -*-

from urllib.request import urlopen
from pymongo import MongoClient
import json
import configparser
import logging  
import logging.config
import time
import re

#from NewsAgency import cnn, the_new_york_times, independent, bbc_news, abc_news_au
#from NewsAgency import usa_today, reuters, football_italia, daily_mail, business_insider_uk
#from NewsAgency import bloomberg, associated_press

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

API_KEY = cfg['NEWS_ACCESS']['API_KEY']
ACCESS_URL_AGENCY = 'https://newsapi.org/v1/sources?language=en&apiKey=' + API_KEY 
ACCESS_URL_ARTICLE = 'https://newsapi.org/v1/articles?source={0}&sortBy={1}&apiKey=' + API_KEY

# stopwords
STOP_WORDS = cfg['NLTK']['STOP_WORDS']
# stop words list
STOP_WORDS = [x.strip() for x in STOP_WORDS.split(',')]
# agency list
agencyIdList = [ x.strip() for x in cfg['PARSE_LIST']['AGENCY_ID'].split(',')]
# country id/name dictionary
COUNTRY = dict(cfg['COUNTRY'].items())

def getAgencies(): 
    resp = urlopen(ACCESS_URL_AGENCY)
    jsn = json.loads(resp.read().decode('utf8'))
    for agency in jsn['sources']:
        sortTypes = agency['sortBysAvailable']
        # latest articles as priority selection
        if 'latest' in sortTypes:
            sort = 'latest'
        else:
            sort = sortTypes[0]
        logger.info('Deal with agency [{0}] - start'.format(agency['id']))
        getArticles(agency['id'], agency['name'], sort, agency['category'], agency['country'])
        logger.info('Deal with agency [{0}] - end'.format(agency['id']))
        logger.info('Sleep for 60s')
        logger.info('-' * 50)
        time.sleep(60)
    
def getArticles(agencyId, agencyName, sort, category, country):
    newsList_url = ACCESS_URL_ARTICLE.format(agencyId, sort)
    logger.info('News List - {0}'.format(newsList_url))
    resp = urlopen(newsList_url)
    jsn = json.loads(resp.read().decode('utf8'))
    for news in jsn['articles']:
        insertToTab(agencyId, agencyName, news['author'], news['title'], news['description'], news['url'], news['urlToImage'], news['publishedAt'], category, country)
        
def insertToTab(agencyId, agencyName, author, title, description, url, urlToImage, publishedAt, category, country):
    # if the article exists already (has same URL or same title)
    if None != db.news.find_one({ '$or': [ {'url': url}, {'title': title} ] }):
        logger.info('Article has already existed - ' + url)
        return
    
    '''------------------------------------------------------------------
    logger.info('Article - ' + url)
    # due to not allow to use '-' in python filename
    agencyId = agencyId.replace('-','_')
    
    # get news content and its summary
    summary, content = '',''
    if agencyId in agencyIdList:
        pars = "{0}.getSummaryAndContent('{1}')".format(agencyId, url)
        #logger.info(pars)
        try:
            summary, content = eval(pars)
            logger.info('Get news summary & content - DONE')
        except Exception as e:
            logger.error('Get news summary & content - FAILED')
            logger.error(e)
   ------------------------------------------------------------------'''
   
    # do not take news article with empty title
    if title is None or title is '' or title.strip() is '':
        logger.info('Title is empty - ' + url)
        return

    # do not take news article with empty description
    if description is None or description is '' or description.strip() is '':
        logger.info('Description is empty - ' + url)
        return        

    # do not take news article with empty published date
    if publishedAt is None or publishedAt is '' or publishedAt.strip() is '':
        logger.info('publishedAt is empty - ' + url)
        return    
    
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
             # 'summary': summary,
             # 'content': content}
    try:
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
    return list(set(keywords)) # remove duplicated words, and MongoDB accepts LIST only
    
if __name__=="__main__":
    while True:
        getAgencies()
        #logger.info('Finished to work through all agencies - sleep for 30 minutes')
        #time.sleep(30)
