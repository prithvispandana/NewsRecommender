# -*- coding: utf-8 -*-

#! /usr/bin/env python3

import http.cookiejar
import urllib.request
from bs4 import BeautifulSoup
import re

#url = 'https://www.newscientist.com/article/2134814-how-did-london-tower-block-fire-spread-so-fast-and-kill-so-many/'
url = 'https://www.newscientist.com/article/2134334-ocean-plastics-from-haitis-beaches-turned-into-laptop-packaging/'

cj = http.cookiejar.CookieJar()
cj = urllib.request.HTTPCookieProcessor(cj)

opennr = urllib.request.build_opener(cj)
urllib.request.install_opener(opennr)


# bs4 is not strong enough
# the html structure got by bs4 is wrong and need a special deal   
# convert bs4.BeautifulSoup to String

# get the response and convert it from bytes into utf-8 str
response = urllib.request.urlopen(url).read().decode("utf-8")

# delete '</div></div></article></main></body></html>' and str before it


'''
# treat story highlights as its summary
highlights = []
lis = soup.find('ul',{'class':'mol-bullets-with-font'})
for x in lis.find_all('li'):
    highlights.append(re.sub(r'\<.*?\>', '', x.text))
summary = ' ; '.join(highlights)'''


str_soup = ''.join(soup.find_all())



paragraphs = []
div = soup.find('div', {'class':'main-content'})
# somehow TAGS are not exactly as same as ones in firefox
# remove all <div>
[x.extract() for x in div.find_all('div')]

ps = div.find_all('p', None)
for x in ps:
    paragraphs.append(re.sub(r'\<.*?\>', '', x.text))

# news content
content = ''.join(paragraphs)