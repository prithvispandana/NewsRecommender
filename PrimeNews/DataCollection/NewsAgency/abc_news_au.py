# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re

#url = 'http://www.bbc.com/news/world-us-canada-40244607'
#url = 'http://www.abc.net.au/news/2017-06-14/deaths-confirmed-in-24-storey-grenfell-tower-fire/8617158'
#url = 'http://www.abc.net.au/news/2017-06-13/heated-exchange-between-abbott-and-laundy-over-finkel-report/8615354'
#url = 'http://www.abc.net.au/news/2017-06-14/ten-enters-volutary-administration/8617078'

def getSummaryAndContent(url):
    cj = http.cookiejar.CookieJar()
    cj = urllib.request.HTTPCookieProcessor(cj)
    
    opennr = urllib.request.build_opener(cj)
    urllib.request.install_opener(opennr)
    t = urllib.request.urlopen(url)
    soup = BeautifulSoup(t.read(), 'html.parser')
    
    paragraphs = []
    div = soup.find('div', 'article section')
    # somehow TAGS are not exactly as same as ones in firefox
    # remove all <div>
    [x.extract() for x in div.find_all('div')]
    # remove all <p class="topics">
    [x.extract() for x in div.find_all('p', 'topics')]
    # remove all <p class="published">
    [x.extract() for x in div.find_all('p', 'published')]
    
    ps = div.find_all('p', None)
    for x in ps:
        paragraphs.append(re.sub(r'\<.*?\>', '', x.text))
    
    # summary
    summary = paragraphs[0]
    # news content
    content = ''.join(paragraphs[1:])
    
    return summary, content


#--------------test-----------------------------
#a, b = getSummaryAndContent(url)
#print(a)
#print('------------')
#print(b)