# -*- coding: utf-8 -*-

from urllib.request import urlopen
from pymongo import MongoClient
import json
import configparser
import logging  
import logging.config
import time

from NewsAgency import cnn, the_new_york_times, independent, bbc_news, abc_news_au
from NewsAgency import usa_today, reuters, football_italia, daily_mail, business_insider_uk
from NewsAgency import bloomberg, associated_press

# get ready for logging
logging.config.fileConfig('log.cfg')  
logger = logging.getLogger('root')
logger.info('Data Collection Program started to work') 

# connect to MongoDB
client = MongoClient('localhost', 27017)
# Database Name: news_db
db = client['news_db']
logger.info('Connected to MongoDB successfully') 

# read from config file
cfg = configparser.ConfigParser()
cfg.read('news.cfg')
cfg.sections()

API_KEY = cfg['NEWS_ACCESS']['API_KEY']
ACCESS_URL_AGENCY = 'https://newsapi.org/v1/sources?language=en&apiKey=' + API_KEY 
ACCESS_URL_ARTICLE = 'https://newsapi.org/v1/articles?source={0}&sortBy={1}&apiKey=' + API_KEY


agencyIdList = [ x.strip() for x in cfg['PARSE_LIST']['AGENCY_ID'].split(',')]

def getAgencies(): 
    resp = urlopen(ACCESS_URL_AGENCY)
    jsn = json.loads(resp.read())
    for agency in jsn['sources']:
        sortTypes = agency['sortBysAvailable']
        # latest articles as priority selection
        if 'latest' in sortTypes:
            sort = 'latest'
        else:
            sort = sortTypes[0]
        logger.info('Deal with agency [{0}] - start'.format(agency['id']))
        getArticles(agency['id'], sort, agency['category'])
        logger.info('Deal with agency [{0}] - end'.format(agency['id']))
        logger.info('Sleep for 60s')
        logger.info('-' * 50)
        time.sleep(60)
    
def getArticles(agencyId, sort, cagtegory):
    newsList_url = ACCESS_URL_ARTICLE.format(agencyId, sort)
    logger.info('News List - {0}'.format(newsList_url))
    resp = urlopen(newsList_url)
    jsn = json.loads(resp.read())
    for news in jsn['articles']:
        insertToTab(agencyId, news['author'], news['title'], news['description'], news['url'], news['urlToImage'], news['publishedAt'], cagtegory)
        
def insertToTab(agencyId, author, title, description, url, urlToImage, publishedAt, cagtegory):
    # if the article exists already
    if None != db.news.find_one({'url': url}):
        logger.info('Article has already existed - ' + url)
        return
    
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

    entity = {'agencyId': agencyId,
              'author': author,
              'title': title,
              'description': description,
              'url': url,
              'urlToImage': urlToImage,
              'publishedAt': publishedAt,
              'cagtegory': cagtegory,
              'summary': summary,
              'content': content}
    try:
        db.news.insert_one(entity)  
        logger.info('Write into DB - DONE')
    except Exception as e:
        logger.error('Write into DB - FAILED')
        logger.error(e)
    
if __name__=="__main__":
    while True:
        getAgencies()
        #logger.info('Finished to work through all agencies - sleep for 30 minutes')
        #time.sleep(30)