# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re

#url = 'http://www.bbc.com/news/world-us-canada-40244607'
#url = 'http://www.bbc.com/news/world-us-canada-40243184'

def getSummaryAndContent(url):
    cj = http.cookiejar.CookieJar()
    cj = urllib.request.HTTPCookieProcessor(cj)
    
    opennr = urllib.request.build_opener(cj)
    urllib.request.install_opener(opennr)
    t = urllib.request.urlopen(url)
    soup = BeautifulSoup(t.read(), 'html.parser')

    # treat introduction as its summary
    intro = []
    for x in soup.find_all('p','story-body__introduction'):
        intro.append(re.sub(r'\<.*?\>', '', x.text))
    summary = ' ; '.join(intro)
    
    # main body of news content
    paragraphs = []
    div = soup.find('div', 'story-body__inner')
    ps = div.find_all('p', None)
    for x in ps:
        paragraphs.append(re.sub(r'\<.*?\>', '', x.text))
    
    content = ''.join(paragraphs)
    
    return summary, content

#--------------test-----------------------------
#a, b = getSummaryAndContent(url)
#print(a)
#print('------------')
#print(b)