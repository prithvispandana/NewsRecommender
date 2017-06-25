import pymongo
client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db



POST_USERNAME = 'realDonaldTrump'



interest_result = db.keyword.find({'user' : POST_USERNAME})
for obj in interest_result:
    res = obj['top_keywords']

list4 = []
for i in res:
    if db.news_new.find({'description' : i}) != None:
        resultset = db.news_new.find({'description' : i})
        for k in resultset:
            list4.append(k)
    else:
            continue

interest_result = db.interest.find({'user' : POST_USERNAME})
for obj in interest_result:
    res = obj['interest']

for i in res:
    if db.news_new.find({'cagtegory' : i}) != None:
        resultset = db.news_new.find({'cagtegory' : i})
        for k in resultset:
            list4.append(k)
    else:
        continue

interest_result = db.interest_similar_user.find({'user' : POST_USERNAME})
for obj in interest_result:
    res = obj['interest']

for i in res:
    if db.news_new.find({'description' : i}) != None:
        resultset = db.news_new.find({'description' : i})
        for k in resultset:
            list4.append(k)
    else:
        continue

#To remove duplcate articles
list5 = [i for n, i in enumerate(list4) if i not in list4[n + 1:]] #https://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python?noredirect=1&lq=1

#to save articles back to the db
collection = db['display_coll']
if "display_coll" in db.collection_names():
	db.display_coll.drop()
	db.display_coll.insert_many(list5)
else:
	db.display_coll.insert_many(list5)


#ordering and displaying
res = db.display_coll.find().sort("publishedAT", -1 )

for k in res:
	print(k)
