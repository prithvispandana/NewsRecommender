from flask import Flask, render_template, url_for, request, session, redirect, jsonify, json
#from flask.ext.pymongo 
from flask_cors import CORS
import pymongo
import bcrypt
import json
#new imports
from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from model import clf, count_vect, tfidf_transformer, twenty_train
import tweepy #https://github.com/tweepy/tweepy
import csv
import pymongo

from sklearn.feature_extraction.text import CountVectorizer
import nltk
import math

from sklearn.feature_extraction import text

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import os.path
from bson import json_util, ObjectId
from bson.json_util import dumps

#Twitter API credentials
consumer_key = "dWUQupK3yWLLAXReEKPUMLlwd"
consumer_secret = "985JhwgsTdzAgGBu6A6I2bTcgEVtLmKq23LMjrWRRrYNyOlf9s"
access_key = "90865238-Zon9cVIb8y3Ai6Qxv1t554kCQPDJr70M4haRrP6be"
access_secret = "eiAiw2xTlDeWzj4uazKWbKaKTAEOXFLw2FBHBsfFchMEJ"




app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'mongologinexample'
app.config['MONGO_URI'] = 'mongodb://pretty:printed@ds021731.mlab.com:21731/mongologinexample'

#mongo = PyMongo(app)
CORS(app)
client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return render_template('afterlogin.html')


@app.route('/login', methods=['POST'])  
def login():
    #users = mongo.db.users
    login_user = db.users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            session['logged_in'] = True
            return redirect(url_for('index'))

    return 'Invalid username/password combination'

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        #users = mongo.db.users
        existing_user = db.users.find_one({'name' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            db.users.insert({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        
        return 'That username already exists!'

    return render_template('register.html')


@app.route('/afterlogin', methods=['GET', 'POST'])
def get_all():
    global POST_USERNAME
    POST_USERNAME = str(request.form['username'])
    return render_template('landing.html')

@app.route('/recom', methods=['GET', 'POST'])
def get_all_tweets():
    #Twitter only allows access to a users most recent 3240 tweets with this method
    
    #authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    #initialize a list to hold all the tweepy Tweets
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = POST_USERNAME,count=200)
    
    #save most recent tweets
    alltweets.extend(new_tweets)
    

    

    # Mongo initialization
    client = pymongo.MongoClient("localhost", 27017)

    db = client.tweets_db
    for s in alltweets:
        if db.twtt.find_one({'text':s.text}) == None: # prevent duplicate tweets being stored
            twtt = {'text':s.text, 'id':s.id, 'created_at':s.created_at,'screen_name':s.author.screen_name,'author_id':s.author.id}
            #print("THE TYPE IS :",type(i))
            db.twtt.insert_one(twtt)


    pass

   
    stopwords = text.ENGLISH_STOP_WORDS
    tokenize = CountVectorizer().build_tokenizer()

    list1 = []
    list2 = []
    result = db.twtt.find({'screen_name' : POST_USERNAME})
    #s = ""
    for obj in result:
        s = ""
        #s = s +" "+ obj['text']
        list1.append(obj['text'])
        s = obj['text']
        tokens1 = tokenize(s.lower())
        
    

    #Removing stop words
        filtered_tokens1 = [word for word in tokens1 if word not in stopwords]
    #finallist.append(filtered_tokens1)
        list2.append(filtered_tokens1)




    final_doc_list2 = []
    #s = ""
    for i in list2:
        temp = " ".join(i)
        final_doc_list2.append(temp)    
    #print(list1)
    #print(tokens1)

  

    vectorizer2 = TfidfVectorizer()
    Y = vectorizer2.fit_transform(final_doc_list2)
    indices = np.argsort(vectorizer2.idf_)[::-1]
    features = vectorizer2.get_feature_names()
    top_n = 50
    top_features = [features[i] for i in indices[:top_n]]
    #print (top_features)
    #print(finallist)   
    #for j in list2:
    #   print(j)
    #db.keyword.create_index([ ('user', 1) ],unique = True)#https://jira.mongodb.org/browse/PYTHON-953,http://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.create_index
    if db.keyword.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.keyword.save({ 'user' : POST_USERNAME,'top_keywords' : top_features})
    else:
        db.keyword.update_one({'user': POST_USERNAME},{'$set':{'top_keywords' : top_features}})

    categories = ['alt.atheism', 'soc.religion.christian','comp.graphics', 'sci.med','talk.politics.misc','sci.space','sci.electronics','talk.politics.mideast','talk.politics.misc']


    docs_new = final_doc_list2
    
    X_new_counts = count_vect.transform(docs_new)
    X_new_tfidf = tfidf_transformer.transform(X_new_counts)

    predicted = clf.predict(X_new_tfidf)

    category_list = []
    for doc, category in zip(docs_new, predicted):
        category_list.append(twenty_train.target_names[category])
        #print('%r => %s' % (doc, twenty_train.target_names[category]))
    category_list = list(set(category_list))
    

    final_category_list = []
    #db.interest.save({ 'user':POST_USERNAME,'interest': category_list})
    for i in category_list:
#         if i == 'talk.politics.misc':
#             final_category_list.append("business")
        if i == 'sci.electronics':
            final_category_list.append('electronics')
        elif i == 'comp.graphics':
             final_category_list.append('computer')
        elif i == 'misc.forsale':
            final_category_list.append('general')
#         elif i == 'talk.politics.guns' or i == 'talk.politics.mideast':
#             final_category_list.append('politics')
        elif i == 'sci.crypt' or i == 'sci.space' or i == 'sci.med':
            final_category_list.append('science-and-nature')
        elif i == 'rec.autos' or i == 'rec.sport.baseball' or i == 'rec.sport.hockey':
            final_category_list.append('sport')   
        elif i == 'comp.windows.x' or i == 'comp.sys.mac.hardware':
            final_category_list.append('hardware')

        #pass
    final_category_list = list(set((final_category_list)))    
    if db.interest.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.interest.save({ 'user' : POST_USERNAME,'interest' : final_category_list})
    else:
        db.interest.update_one({'user': POST_USERNAME},{'$set':{'interest' : final_category_list}})



    document_writing_list_combined = final_category_list + top_features

    
    save_path = R'files'   
    completeName = os.path.join(save_path, POST_USERNAME+".txt")         
    file1 = open(completeName, "w",encoding='utf8')
    for i in document_writing_list_combined:
        file1.write(i+'\n')
    file1.close()

###############################################################################################################3333


    #globvar = 0.02
   #top N similar user from smilarity matrix
    from user_sim_matrix_calc import getTopN
    topNUsers=getTopN(POST_USERNAME+".txt",2)
    uniset=set()
    for top in topNUsers:
        fileName = os.path.join(save_path, top) 
        if not fileName:
            continue
        else:
            uniset.update(set(open(fileName).read().split())) 
        
    #substract from original
    fileName = os.path.join(save_path, POST_USERNAME+".txt")
    origin=set(open(fileName).read().split())
    result_set=origin-uniset

    interest_result = db.keyword.find({'user' : POST_USERNAME})
    for obj in interest_result:
        res = obj['top_keywords']

    list4 = []
    for i in res:
        if db.news_new.find({'keywords' : i}) != None:
            resultset = db.news_new.find({'keywords' : i})
        for k in resultset:
            list4.append(k)
        else:
            continue
        
    #other similar user 
    for i in result_set:
        if db.news_new.find({'keywords' : i}) != None:
            resultset = db.news_new.find({'keywords' : i})
            for k in resultset:
                list4.append(k)
            else:
                continue
            
    list5 = [i for n, i in enumerate(list4) if i not in list4[n + 1:]]
    
    #to save articles back to the db
    collection = db['display_coll']
    if "display_coll" in db.collection_names():
        db.display_coll.drop()
        db.display_coll.insert_many(list5)
    else:
        db.display_coll.insert_many(list5)


#ordering and displaying
    hybrid = db.display_coll.find().sort("publishedAt", -1 )
    return dumps(hybrid)
#     print(dumps(hybrid))
#     try:
#         recomList = []
#         for recomd in hybrid:
#             recomItem = {
#                     '_id':{"$oid":recomd['_id']},
#                     'author':recomd['author'],
#                     'cagtegory':recomd['cagtegory'],
#                     'description':recomd['description'],
#                     'publishedAt':recomd['publishedAt'],
#                     'title':recomd['title'],
#                     'url':recomd['url'],
#                     'urlToImage':recomd['urlToImage']
#                     }
#             recomList.append(recomItem)
#     except Exception as e:
#         return str(e)
#     return json.dumps(recomList)


    #     return render_template('hom.html',output = dumps(res))
#     return "done"

@app.route("/home")
def hello():
    return render_template("home.html")

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return index()

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host='0.0.0.0', debug=True, port=9000)

    