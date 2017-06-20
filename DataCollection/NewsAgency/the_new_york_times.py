# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re

#url = 'https://www.nytimes.com/2017/06/03/world/asia/afghanistan-explosion-funeral.html'
#url = 'https://www.nytimes.com/2017/05/14/business/economy/home-ownership-turnover.html'
url = 'https://www.nytimes.com/2017/06/13/us/politics/jeff-sessions-testimony.html?_r=0&mtrref=newsapi.org&gwh=8C64A614DACA2E48A02E2D7FDF13D643&gwt=pay'

def getSummaryAndContent(url):
    cj = http.cookiejar.CookieJar()
    cj = urllib.request.HTTPCookieProcessor(cj)
    
    opennr = urllib.request.build_opener(cj)
    urllib.request.install_opener(opennr)
    t = urllib.request.urlopen(url)
    soup = BeautifulSoup(t.read(), 'html.parser')
    paragraphs = []
    for x in soup.find_all('p','story-body-text story-content'):
        # no good to use x.string, because it will lose words with href link
        #print(x.string)
        paragraphs.append(re.sub(r'\<.*?\>', '', x.text))
    
    # summary
    summary = paragraphs[0]
    # content
    content = ''.join(paragraphs)
    
    return summary, content
    
#--------------test-----------------------------
#a, b = getSummaryAndContent(url)
#print(a)
#print('------------')
#print(b)