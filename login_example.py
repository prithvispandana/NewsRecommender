from flask import Flask, render_template, url_for, request, session, redirect, jsonify, json
from flask_cors import CORS
import bcrypt
import json
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from model import clf, count_vect, tfidf_transformer, twenty_train
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

from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer

import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
from gensim import corpora, models
import gensim

#new imports
from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort,url_for
import os

import tweepy #https://github.com/tweepy/tweepy
from sklearn.feature_extraction.text import CountVectorizer

from nltk.tokenize import TweetTokenizer
import itertools

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

    #Liked Tweets
    likes_list = []
    for like in tweepy.Cursor(api.favorites,screen_name = POST_USERNAME,count=200).items(): #https://stackoverflow.com/questions/42420900/how-to-get-all-liked-tweets-by-a-user-using-twitter-api
        likes_list.append(like)

    total_tweets = alltweets + likes_list

    #Hashtags from all the tweets
    listy = []
    hashy = []
    for i in total_tweets:
        listy = [j['text'] for j in i.entities.get('hashtags')]
        if not listy:
            continue
        else:
            for k in listy:
                hashy.append(k.lower())

    hashtags_list = list(set(hashy))

    #Mongo initialization
    client = pymongo.MongoClient("localhost", 27017)
    db = client.tweets_db
    #save the hashtags
    if db.hashtags.find_one({'user':POST_USERNAME}) == None: # prevent duplicate being stored
        db.hashtags.save({ 'user' : POST_USERNAME,'hashtags' : hashtags_list})
    else:
        db.hashtags.update_one({'user': POST_USERNAME},{'$set':{'hashtags' : hashtags_list}})

    import re
    #Saving all tweets
    
    for s in total_tweets:
        if db.twtt.find_one({'text':s.text}) == None: # prevent duplicate tweets being stored
            twtt = {'text':s.text, 'id':s.id, 'created_at':s.created_at,'screen_name':s.author.screen_name,'author_id':s.author.id}
            try:
                db.twtt.insert_one(twtt)
            except:
                print("Cant be loaded")
    pass

    #### Tweet processing
    from sklearn.feature_extraction import text
    stopwords = text.ENGLISH_STOP_WORDS
    tokenize = CountVectorizer().build_tokenizer()

    list1 = []
    list2 = []
    result = db.twtt.find({'screen_name' : POST_USERNAME})

    for obj in result:
        s = ""
        list1.append(obj['text'])
        s = obj['text']

        tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
        l1 = tknzr.tokenize(s.lower())

        #Removing stop words
        l1 = [word for word in l1 if word not in stopwords]

        r = re.compile("http.*")
        new_list = filter(r.match, l1)
        for i in list(new_list):
            l1.remove(i)

        hashtag_list = []
        r = re.compile("#.*")
        new_list = filter(r.match, l1)

        hashtags_list = [x[1:] for x in new_list if x in l1]
        without_hashtags_list = [s for s in l1 if "#" not in s]

        cleaned_tweet  =  hashtags_list + without_hashtags_list
        stringss = " ".join(cleaned_tweet)
        new = re.sub(r'[^A-Za-z]', ' ', stringss)
        new = new.split()

        #selfmade dictionary for removing some words
        from nltk.corpus import words
        proper_list = [word for word in new if word not in ['time','way','good','thank','big','bad','new','today','join',
        's','rt','t','th','u','w','g','a','ve',"a",'b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r',
        's','t','u','v','w','x','y','z',"sources","just","did" ,"about", "above", "above", "across", "after", 
        "afterwards", "again", "against", "all", "almost", "alone", "along", "already", "also","although","always","am",
        "among", "amongst", "amoungst", "amount",  "an", "and", "another", "any","anyhow","anyone","anything","anyway",
        "anywhere", "are", "around", "as",  "at", "back","be","became", "because","become","becomes", "becoming", "been", 
        "before", "beforehand", "behind", "being", "below", "beside", "besides", "between", "beyond", "bill", "both", "bottom",
        "but", "by", "call", "can", "cannot", "cant", "co", "con", "could", "couldnt", "cry", "de", "describe", "detail", "do", 
        "done", "down", "due", "during", "each", "eg", "eight", "either", "eleven","else", "elsewhere", "empty", "enough", "etc", 
        "even", "ever", "every", "everyone", "everything", "everywhere", "except", "few", "fifteen", "fify", "fill", "find", "fire", 
        "first", "five", "for", "former", "formerly", "forty", "found", "four", "from", "front", "full", "further", "get", "give", "go", 
        "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "him", 
        "himself", "his", "how", "however", "hundred", "ie", "if", "in", "inc", "indeed", "interest", "into", "is", "it", "its", "itself", 
        "keep", "last", "latter", "latterly", "least", "less", "ltd", "made", "many", "may", "me", "meanwhile", "might", "mill", "mine", 
        "more", "moreover", "most", "mostly", "move", "much", "must", "my", "myself", "name", "namely", "neither", "never", "nevertheless", 
        "next", "nine", "no", "nobody", "none", "noone", "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once", "one", 
        "only", "onto", "or", "other", "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own","part", "per", "perhaps", 
        "please", "put", "rather", "re", "same", "see", "seem", "seemed", "seeming", "seems", "serious", "several", "she", "should", 
        "show", "side", "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone", "something", "sometime", "sometimes", 
        "somewhere", "still", "such", "system", "take", "ten", "than", "that", "the", "their", "them", "themselves", "then", "thence", 
        "there", "thereafter", "thereby", "therefore", "therein", "thereupon", "these", "they", "thickv", "thin", "third", "this", "those", 
        "though", "three", "through", "throughout", "thru", "thus", "to", "together", "too", "top", "toward", "towards", "twelve", "twenty", 
        "two", "un", "under", "until", "up", "upon", "us", "very", "via", "was", "we", "well", "were", "what", "whatever", "when", "whence", 
        "whenever", "where", "whereafter", "whereas", "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", 
        "who", "whoever", "whole", "whom", "whose", "why", "will", "with", "within", "without", "would", "yet", "you", "your", "yours", 
        "yourself", "yourselves", "the"]]
        list2.append(proper_list)


    final_doc_list2 = []
    for i in list2:
        temp = " ".join(i)
        final_doc_list2.append(temp)    

    user = api.get_user(POST_USERNAME)


    #Followings of the user
    friend_list = []
    for friend in tweepy.Cursor(api.friends,screen_name = POST_USERNAME,count=200).items(): #https://stackoverflow.com/questions/25944037/full-list-of-twitter-friends-using-python-and-tweepy
        # Process the friend here
        friend_list.append(friend.screen_name)

    #save the followings
    if db.followings.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.followings.save({ 'user' : POST_USERNAME,'friends' : friend_list})
    else:
        db.followings.update_one({'user': POST_USERNAME},{'$set':{'friends' : friend_list}})

    #LDA
    texts = list2
    # turn our tokenized documents into a id <-> term dictionary
    dictionary = corpora.Dictionary(texts)
    # convert tokenized documents into a document-term matrix
    corpus = [dictionary.doc2bow(text) for text in texts]

    # generate LDA model
    ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=50, id2word = dictionary, passes=10)
    cool = ldamodel.print_topics(num_topics=50, num_words=1)

    lda_list = []
    lda = [tup[1] for tup in cool]
    for i in lda:
        lda_list.append(re.sub(r'[^A-Za-z]', '', i))
    lda_list = list(set(lda_list))

    #save LDA topics
    if db.ldatopics.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.ldatopics.save({ 'user' : POST_USERNAME,'topics' : lda_list})
    else:
        db.ldatopics.update_one({'user': POST_USERNAME},{'$set':{'topics' : lda_list}})

    #   print(j)
    #db.keyword.create_index([ ('user', 1) ],unique = True)#https://jira.mongodb.org/browse/PYTHON-953,http://api.mongodb.com/python/current/api/pymongo/collection.html#pymongo.collection.Collection.create_index
    # if db.keyword.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
    #     db.keyword.save({ 'user' : POST_USERNAME,'top_keywords' : top_features})
    # else:
    #     db.keyword.update_one({'user': POST_USERNAME},{'$set':{'top_keywords' : top_features}})

    #Classification using BBC
    category_list = []
    docs_new = final_doc_list2
    X_new_counts = count_vect.transform(docs_new)
    X_new_tfidf = tfidf_transformer.transform(X_new_counts)

    predicted = clf.predict(X_new_tfidf)

    for doc, category in zip(docs_new, predicted):
        category_list.append(twenty_train.target_names[category])
        #print('%r => %s' % (doc, twenty_train.target_names[category]))
    
    final_category_list = []
    counts = dict()
    for i in category_list:
        counts[i] = counts.get(i, 0) + 1
        if i == 'tech':
            final_category_list.append("technology")
        else:
            final_category_list.append(i)


    print(counts)


    length_list = len(category_list)
    for i in counts:
        counts[i] = counts.get(i)/length_list

    print(counts)


    final_category_list = list(set(final_category_list))

    if db.interest.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.interest.save({ 'user' : POST_USERNAME,'interest' : final_category_list})
    else:
        db.interest.update_one({'user': POST_USERNAME},{'$set':{'interest' : final_category_list}})

    document_writing_list_combined = final_category_list + lda_list + hashtags_list#+ top_features
    
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

    interest_result = db.ldatopics.find({'user' : POST_USERNAME})
    for obj in interest_result:
        res = obj['topics']

    list4 = []
    for i in res:
        print(i)
        if db.news_new.find({'keywords' : i}) != None:
            resultset = db.news_new.find({'keywords' : i})
            for k in resultset:
                list4.append(k)
        else:
            continue
        
    #other similar user 
    # for i in result_set:
    #     if db.news_new.find({'keywords' : i}) != None:
    #         resultset = db.news_new.find({'keywords' : i})
    #         for k in resultset:
    #             list4.append(k)
    #         else:
    #             continue
            
    list5 = [i for n, i in enumerate(list4) if i not in list4[n + 1:]] # to remove duplicate articles
    
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

    