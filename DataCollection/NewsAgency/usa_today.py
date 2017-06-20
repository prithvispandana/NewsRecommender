# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re

#url = 'https://www.usatoday.com/story/life/people/2017/06/14/bill-cosby-jury-deliberations-taking-long-meaning/102848942/'

def getSummaryAndContent(url):
    cj = http.cookiejar.CookieJar()
    cj = urllib.request.HTTPCookieProcessor(cj)
    
    opennr = urllib.request.build_opener(cj)
    urllib.request.install_opener(opennr)
    t = urllib.request.urlopen(url)
    soup = BeautifulSoup(t.read(), 'html.parser')
    '''
    # treat story highlights as its summary
    highlights = []
    lis = soup.find('ul',{'class':'mol-bullets-with-font'})
    for x in lis.find_all('li'):
        highlights.append(re.sub(r'\<.*?\>', '', x.text))
    summary = ' ; '.join(highlights)'''
        
    paragraphs = []
    div = soup.find('div', {'itemprop':'articleBody'})
    # somehow TAGS are not exactly as same as ones in firefox
    # remove all <div>
    [x.extract() for x in div.find_all('div')]
    
    ps = div.find_all('p', None)
    for x in ps:
        paragraphs.append(re.sub(r'\<.*?\>', '', x.text))
    
    # summary
    summary = paragraphs[0]
    # news content
    content = ''.join(paragraphs)
    
    return summary, content

#--------------test-----------------------------
#a, b = getSummaryAndContent(url)
#print(a)
#print('------------')
#print(b)