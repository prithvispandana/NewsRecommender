# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re
import logging 
import traceback

logger = logging.getLogger('main.cnn')  

#url = 'http://www.independent.co.uk/news/uk/politics/tory-dup-deal-latest-news-grenfell-tower-fire-no-announcement-london-kensington-conservatives-a7789116.html'
#url = 'http://www.independent.co.uk/news/uk/home-news/london-fire-latest-grenfell-tower-block-dead-deaths-kensington-met-police-a7789221.html'
#url = 'http://edition.cnn.com/2017/06/14/politics/alexandria-virginia-shooting/index.html'
#url = 'http://edition.cnn.com/videos/us/2017/06/14/jeff-flake-baseball-practice-shooting-sot-newday.cnn'
#url = 'http://edition.cnn.com/2017/06/14/politics/gabby-giffords-tweet/index.html'

def getSummaryAndContent(url):
    try:
        cj = http.cookiejar.CookieJar()
        cj = urllib.request.HTTPCookieProcessor(cj)
        
        opennr = urllib.request.build_opener(cj)
        urllib.request.install_opener(opennr)
        t = urllib.request.urlopen(url)
        soup = BeautifulSoup(t.read(), 'html.parser')
        
        # treat story highlights as its summary
        highlights = []
        lis = soup.find_all('li',{'class':'el__storyhighlights__item'})
        for x in lis:
            highlights.append(re.sub(r'\<.*?\>', '', x.text))
        summary = ' ; '.join(highlights)
        
        # the first part of news content
        head = soup.find('p', {'class':'zn-body__paragraph speakable'})
        head = re.sub(r'\<.*?\>', '', head.text)
        # the main part of news content
        paragraphs = []
        ps = soup.find_all('div', {'class':'zn-body__paragraph'})
        for x in ps:
            paragraphs.append(re.sub(r'\<.*?\>', '', x.text))
        content = ''.join(paragraphs)
        logger.info('Parsing CNN web page - DONE - ' + url)
        
        return summary, head + content
    except:
        logger.info('Parsing CNN web page - FAILED - ' + url)
        logger.info(traceback.print_exc())
        return '',''
    

#--------------test-----------------------------
#a, b = getSummaryAndContent(url)
#print(a)
#print('------------')
#print(b)