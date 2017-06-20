# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re

#url = 'http://www.independent.co.uk/news/uk/politics/tory-dup-deal-latest-news-grenfell-tower-fire-no-announcement-london-kensington-conservatives-a7789116.html'
#url = 'http://www.independent.co.uk/news/uk/home-news/london-fire-latest-grenfell-tower-block-dead-deaths-kensington-met-police-a7789221.html'
#url = 'http://www.independent.co.uk/news/uk/home-news/london-fire-grenfell-tower-cladding-architects-firefighters-experts-reason-why-cause-a7789336.html'


def getSummaryAndContent(url):
    cj = http.cookiejar.CookieJar()
    cj = urllib.request.HTTPCookieProcessor(cj)
    
    opennr = urllib.request.build_opener(cj)
    urllib.request.install_opener(opennr)
    t = urllib.request.urlopen(url)
    soup = BeautifulSoup(t.read(), 'html.parser')
    
    paragraphs = []
    div = soup.find('div', {'class':'text-wrapper'})
    [x.extract() for x in div.find_all('div')]
    
    ps = div.find_all('p', None)
    for x in ps:
        paragraphs.append(re.sub(r'\<.*?\>', '', x.text))
    
    # summary
    summary = paragraphs[0]
    # content
    content = ''.join(paragraphs[1:])
    
    return summary, content


#--------------test-----------------------------
#a, b = getSummaryAndContent(url)
#print(a)
#print('------------')
#print(b)