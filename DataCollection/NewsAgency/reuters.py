# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re

#url = 'http://www.reuters.com/article/us-usa-trump-russia-idUSKBN195385'

def getSummaryAndContent(url):
    cj = http.cookiejar.CookieJar()
    cj = urllib.request.HTTPCookieProcessor(cj)
    
    opennr = urllib.request.build_opener(cj)
    urllib.request.install_opener(opennr)
    t = urllib.request.urlopen(url)
    soup = BeautifulSoup(t.read(), 'html.parser')
    
    paragraphs = []
    div = soup.find('span', {'id':'article-text'})
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