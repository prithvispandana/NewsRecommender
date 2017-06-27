#script for updating the description of news documents for implementing keyword search

import pymongo
client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db
keyword_result = db.news.find()
for obj in keyword_result:
    _id= obj['_id']
    url = obj['url']
    title= obj['title']
    publishedAT= obj['publishedAt']
    author= obj['author']
    category= obj['cagtegory']
    urlToImage= obj['urlToImage']
    description = obj['description']
    if description == None:
        continue
    else:
        keywordslist = description.split()
        db.news_new.save({ '_id' : _id,'publishedAT' : publishedAT,'title' : title,'author' : author,'description' : description,'keywords' : keywordslist,'url' : url,'urlToImage':urlToImage,'category':category})

