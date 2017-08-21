import pymongo
from bson.json_util import dumps, ObjectId
from flask import jsonify
client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db


def searchNews(data,userName):
    searchlist = data['search'].split()
    if db.searchsave.find_one({'user':userName}) == None: # prevent duplicate tweets being stored
        db.searchsave.save({ 'user' : userName,'keywords' : searchlist})
    elif len(searchlist)>1:
        db.searchsave.update_one({'user': userName},{'$set':{'keywords' : searchlist}})
    
    db.news.ensure_index([
        ('title', 'text'),
        ('description', 'text'),
    ],
        name="TextIndex",
        weights={
            'title': 3,
            'description': 1
        }
    )
    results=db.news.find({"$text":{"$search":data['search'],"$caseSensitive": False, }})
    print(results)
    array=[]
    arr=[]
    for obj in results:
        coll = {'title': obj['title'],
                'url': obj['url'],
                'description':obj['description'],
                'image':obj['urlToImage'],
                'agency':obj['agencyName'],
                'date':obj['publishedAt']}
        array.append(coll)

    return dumps(array)


def save_userNews(data,userName):
    if db.usernews.find_one({'newsId':data['newsId'],'userId':userName}) is None:
        print('Document not found.Ready to insert')
        db.usernews.insert_one(data)
        print('Document Inserted')
    else:
        print("Document Already exists")

    return jsonify({ "status": "ok"})

    # return jsonify({ "status": "ok"})


def get_userNews(userid):
    # get from db db.usernews
    news = db.usernews.find({ "userId": userid})
    articles = []
    for obj in news:
        art = db.news.find_one( ObjectId(obj['newsId'] ))
        articles.append(art)
    return dumps(articles)



def save_userlikes(data, userName):
    if db.userslikes.find_one({'newsId': data['newsId'], 'userId': userName}) is None:
        print('Document not found.Ready to insert')
        db.userslikes.insert_one(data)
        if db.usersdislikes.find_one({'newsId': data['newsId'], 'userId': userName}) is not None:
            db.usersdislikes.delete_one( {'newsId': data['newsId'], 'userId': userName});
        print('Document inserted')
    else:
        print("Document Already exists")
    return jsonify({ "status": "ok"})


def save_usersdislikes(data,userName): 
    if db.usersdislikes.find_one({'newsId': data['newsId'], 'userId': userName}) is None:
        print('Document not found.Ready to insert')
        db.usersdislikes.insert_one(data)
        if db.userslikes.find_one({'newsId': data['newsId'], 'userId': userName}) is not None:
            db.userslikes.delete_one( {'newsId': data['newsId'], 'userId': userName});
        print('Document inserted')
    else:
        print("Document Already exists")
    return jsonify({ "status": "ok"})



def sim_News(data):
    #retrieve the object to find the similar news of it
    data = request.get_json(True)
    
    # get excluded URLs that should not show up in embmed documents
    excURLs = getExcludedURL(data)
    strCategory =data['category']
    strSearch = data['title'] + " " + data['description']
     
    pipeline = [{ "$match": { "url": { "$nin": excURLs},
                              "category": strCategory,
                              "$text": { "$search": strSearch , 
                                         "$caseSensitive": False, 
                                         "$diacriticSensitive": False, 
                                         "$language": "en" } } },
                { "$project": { "_id" : 1,
                                "countryId" : 1, 
                                "countryName" : 1,
                                "keywords" : 1, 
                                "author" : 1, 
                                "description" : 1, 
                                "title" : 1, 
                                "agencyId" : 1, 
                                "agencyName" : 1, 
                                "url" : 1, 
                                "urlToImage" : 1, 
                                "publishedAt" : 1, 
                                "category" : 1,
                                "score": { "$meta": "textScore" } } },
                { "$match": { "score": { "$gt": 3.0 }}},
                { "$sort": { "score": { "$meta": "textScore" }}},
                { "$limit" : 9 }]
    
    cursor = db.news.aggregate(pipeline)
                    
    return dumps(cursor)


def getExcludedURL(jsonData):
    urlList = []
    urlList.append(jsonData['url'])
    return urlList