import pymongo
from bson.json_util import dumps, ObjectId
from flask import jsonify
client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db

'''
This function will be called when user enters search word in the UI
'''
def searchNews(data,userName):
    searchlist = data['search'].split()
    if db.searchsave.find_one({'user':userName}) == None: # prevent duplicate tweets being stored
        db.searchsave.save({ 'user' : userName,'keywords' : searchlist}) #search keywords saved to database
    elif len(searchlist)>1:
        db.searchsave.update_one({'user': userName},{'$set':{'keywords' : searchlist}}) #updated the search keywords
    # To check index is made
    db.news.ensure_index([
        ('title', 'text'),
        ('description', 'text'),
    ],
        name="TextIndex",#Name assigned to the index
        weights={ #Weights assigned to the index 
            'title': 3,
            'description': 1
        }
    )
    results=db.news.find({"$text":{"$search":data['search'],"$caseSensitive": False, }})# Returns all the relative search results
    print(results)
    array=[]
    arr=[]
    for obj in results: #send specific information to frontend
        coll = {'title': obj['title'],
                'url': obj['url'],
                'description':obj['description'],
                'image':obj['urlToImage'],
                'agency':obj['agencyName'],
                'date':obj['publishedAt']}
        array.append(coll)

    return dumps(array)
'''
This function will be called when bookmark symbol is pressed in the UI
'''
def save_userNews(data,userName):
    if db.usernews.find_one({'newsId':data['newsId'],'userId':userName}) is None: # function saves a new usernews document ( data ), if it is not found
        print('Document not found.Ready to insert')
        db.usernews.insert_one(data) #insert data to usernews collection
        print('Document Inserted')
    else:
        print("Document Already exists")

    return jsonify({ "status": "ok"})


'''
This function will be called to get the user news
'''
def get_userNews(userid):
    # get from db db.usernews
    news = db.usernews.find({ "userId": userid}) # Find's the news for the particular user
    articles = []
    for obj in news:
        art = db.news.find_one( ObjectId(obj['newsId'] ))
        articles.append(art)
    return dumps(articles)

'''
This function will be called when liked symbol is pressed in the UI
'''
def save_userlikes(data, userName):
    if db.userslikes.find_one({'newsId': data['newsId'], 'userId': userName}) is None: # function saves a new userlikes document ( data ), if it is not found
        print('Document not found.Ready to insert')
        db.userslikes.insert_one(data)
        if db.usersdislikes.find_one({'newsId': data['newsId'], 'userId': userName}) is not None: #delete news from dislikes to maintain consistency
            db.usersdislikes.delete_one( {'newsId': data['newsId'], 'userId': userName});
        print('Document inserted')
    else:
        print("Document Already exists")
    return jsonify({ "status": "ok"})
'''
This function will be called when disliked symbol is pressed in the UI
'''
def save_usersdislikes(data,userName): 
    if db.usersdislikes.find_one({'newsId': data['newsId'], 'userId': userName}) is None:# function saves a new userdislikes document ( data ), if it is not found
        print('Document not found.Ready to insert')
        db.usersdislikes.insert_one(data)
        if db.userslikes.find_one({'newsId': data['newsId'], 'userId': userName}) is not None: #delete dislikes from likes news
            db.userslikes.delete_one( {'newsId': data['newsId'], 'userId': userName});
        print('Document inserted')
    else:
        print("Document Already exists")
    return jsonify({ "status": "ok"})


'''
Calculate the similarity between a recommended news article and others and get the top N
'''
def sim_News(data):

    # get excluded URLs that should not show up in embmed documents
    excURLs = getExcludedURL(data)
    strCategory =data['category']
    # search by Text Index with all words in TITLE & DESCRIPTION
    # (Text Search function will remove STOP-WORDS and run WORDS STEMMING automatically)
    strSearch = data['title'] + " " + data['description']
    
    # text search on the collection NEWS
    '''
    $search	- Keywords that will be searched on TITLE & DESCRIPTION of collection NEWS
    $caseSensitive - Whether it should be sensitive to uppercase/lowercase
    $diacriticSensitive - Whether it should be sensitive to diacritic, for example, CAFÉ
    $language - he language it will deal with, for example, "en" 
                [ If setting to "en", it will deal with STOP-WORDS and doing WORDS STEMMING based on English Language, 
                  which exactly what NLTK does but more automatically.]
    '''
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
    
    # execute the SQL on MongoDB
    cursor = db.news.aggregate(pipeline)
                    
    return dumps(cursor)

'''
Exclude the URLs of the news articles in recommended news list
'''
def getExcludedURL(jsonData):
    urlList = []
    urlList.append(jsonData['url'])
    return urlList
