from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_cors import CORS
import bcrypt
import pickle
#new imports
import tweepy
import pymongo
from bson.json_util import dumps, ObjectId
from sklearn.feature_extraction import text

import os.path
import spacy
import re

import logging
from logging.handlers import RotatingFileHandler
import datetime

from primeFeatures import searchNews, save_userNews, get_userNews,save_userlikes,save_usersdislikes, sim_News
from util import getTopN, save_friendList, save_hashtag, get_tweets, get_likes, get_mostCommon, get_entities, get_appLikes, get_appsaved
from util import save_uniqueWords, get_tweetIntrest, save_tweetIntrest, save_profile, get_collKeywords,assign_score,recom_hybridarticles, get_normIntrest
from util import get_perCategory, update_perCategory
app = Flask(__name__)
CONSUMER_TOKEN='20WnaxITmExInaxGV7mcFOccJ'
CONSUMER_SECRET='vLNFoj0kEmT0EOGkaWiUg4MJETxI38plzqLHdnb55M7PfUVvSM'
CALLBACK_URL = 'http://127.0.0.1:5000/verify'
sess = dict()
dbp = dict() #you can save these values to a database
stopwords = text.ENGLISH_STOP_WORDS

CORS(app)
#Mongo Db Client and DB
client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db
nlp = spacy.load("en")
topN=2

'''
This method listen all the request which starts with forward slash(/)
if user is already logged in system , then user will redirect to home 
(recommendation article page)otherwise user will redirect to index(login page)
'''
@app.route('/')
def index():
    if not session.get('logged_in'):
        dbp.clear()
        return render_template('index.html')
    elif dbp:
        return render_template('landing.html', user =dbp['screen_name'] , img_url=dbp['prof_url'])
    else:
        dbp.clear()
        return render_template('landing.html', user=session['username'])


'''
This method register the user who doesn't have twitter aaccount can 
register with prime application but this kind of user only get top 
stories and prime appliaction run over time and recommend the news accordingly.
'''
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        #Non twitter users
        existing_user = db.users.find_one({'name' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            db.users.insert({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        return 'That username already exists!'
    return render_template('register.html')


'''
Non twitter users logins to system and validate the user login id 
and password from the databse
'''
@app.route('/login', methods=['POST'])  
def login():
    login_user = db.users.find_one({'name' : request.form['username']})
    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            session['logged_in'] = True
            return redirect(url_for('index'))
    return 'Invalid username/password combination'


'''
Twitter user login to system, To do so user authorised the application 
for access of request token and redirect url from registered prime twitter 
application
'''
@app.route('/login')
def twitterlogin():
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK_URL)    
    try: 
        #get the request tokens
        redirect_url= auth.get_authorization_url()
        session['request_token']= (auth.request_token)
    except tweepy.TweepError:
        print('Error! Failed to get request token')
    return redirect(redirect_url)


'''
After twitter verification, application get the access_token and
access_secret of user and save the api into dictionay for further
use in the application. Method redirected to authorized method
which save the user profile image, screen name, current time zone
and location which account is created.
'''
@app.route("/verify")
def get_verification():    
    #get the verifier key from the request url
    verifier= request.args['oauth_verifier']
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    token = session['request_token']
    #del session['request_token']
    auth.request_token=token
    try:
        verifier = request.args.get('oauth_verifier')
        auth.get_access_token(verifier)
        session['token'] = (auth.access_token, auth.access_token_secret)
        dbp.clear()
        api = tweepy.API(auth)
        session['logged_in'] = True
        #store in a db
        dbp['api']=api
        dbp['access_token_key']=auth.access_token
        dbp['access_token_secret']=auth.access_token_secret
    except tweepy.TweepError:
            print('Error! Failed to get access token.')    
    return redirect(url_for('authorized'))


'''
If user is already logged in system, then user will redirect to landing
(recommendation article page), otherwise user will redirect to index page
'''    
@app.route('/authorized')
def authorized():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        global POST_USERNAME
        api = dbp['api']
        usr =api.me()
        POST_USERNAME=usr.screen_name
        img=usr.profile_image_url
        dbp['screen_name']=POST_USERNAME
        dbp['prof_url']=img
        dbp['acc_location']=usr.location
        dbp['time_zone']=usr.time_zone
        return render_template('landing.html', user=POST_USERNAME, img_url=img)


'''
This method invalidate the user session and redirect to index (login page)
'''
@app.route("/logout")
def logout():
    #session["__invalidate__"] = True
    session.pop('logged_in', None)
    #session['logged_in'] = False
    dbp.clear()
    return index()


'''
This is first page after login and other page will be loded inside
this page using angular js
'''
@app.route("/home")
def home():
    return render_template("home.html")

'''
This method recommend the article for twitter and non twitter user also.
Processing of this method
collect user tweets from twitter
collect user likes from twitter
Collect user friend followings
Collect user hashtag
Collect most common using spacy library 
Predict the user intrest from tweets
Collect colloaborative keywords
collect explicit feedback 
Above all data is saved to user profile 
according to in memory user profile recommendation will be done
'''
@app.route('/recom', methods=['GET', 'POST'])
def get_recommendation():
    try:      
        api = dbp['api']
    except Exception as e:
        dbp.clear()
        gen_user = db.news.find().sort("publishedAt", -1 ).limit(180)
        return dumps(gen_user)
    recom_scoredList=[]
    try:    
        friend_list=save_friendList(api,POST_USERNAME)
        tweets = get_tweets(api, POST_USERNAME)
        liked = get_likes(api,POST_USERNAME)
        tweets.extend(liked)
        document=" ".join(tweets)
        document = nlp(document)
        most_common=get_mostCommon(document)
        entities=get_entities(document)
        most_common.extend(entities)
        processedWords=list(set(most_common))
        save_uniqueWords(processedWords,POST_USERNAME)
        tweet_intrest=get_tweetIntrest(tweets)
        final_intrest_category, normCounts = get_normIntrest(tweet_intrest)
        final_intrest_category = list(set(final_intrest_category))
        save_tweetIntrest(final_intrest_category,POST_USERNAME)
        profile_list_combined = final_intrest_category + processedWords
        save_profile(profile_list_combined,POST_USERNAME)
        result_set=get_collKeywords(topN,POST_USERNAME)
        app_likes=get_appLikes(POST_USERNAME)
        app_saved=get_appsaved(POST_USERNAME)
        final_search_list = list(result_set) + processedWords + app_likes + app_saved
        #cold start user
        if dbp['acc_location'] is not None and dbp['acc_location']!="":
            final_search_list.extend(dbp['acc_location'].split(","))
        if dbp['time_zone'] is not None and dbp['time_zone']!="":    
            final_search_list.extend(dbp['time_zone'].split(","))
        print(final_search_list)  
        search_kwlst = set([ i.lower() for i in final_search_list])
        recom_list = db.news.find({"keywords":{"$in": list(search_kwlst)}})
        recom_scoredList=assign_score(recom_list, normCounts)
        if not recom_scoredList: #If cold start problem is not solved with location and timezone field give top stories
            recom_scoredList = db.news.find().sort("publishedAt", -1 ).limit(180)
    except Exception as e:
        print(e)
        return "Sorry We are not able to process your request this Time"
    return dumps(recom_hybridarticles(recom_scoredList,POST_USERNAME))

'''
This method returns the article which are similar to the recommended article
'''
@app.route('/simNews', methods=['POST'])
def simNews():
    data = request.get_json(True)
    # get similar news articles
    return sim_News(data)

'''
User article is saved and can be read in future fron saved article user interface
'''
@app.route('/usernews', methods=['POST'])
def post_usernews():
    data = request.get_json(True)
    if 'screen_name' in dbp:
        userName = dbp['screen_name']
    else:
        userName = session['username']

    return save_userNews(data,userName)


'''
Saved article is accessed using userid
'''
@app.route('/usernews/<userid>', methods=['GET'])
def get_usernews(userid):
    return get_userNews(userid)


'''
User likes saved into database as a explicit feedback and used 
for future recommendation.
'''
@app.route('/likes', methods=['POST'])
def post_userlikes():
    data = request.get_json(True)
    print(data)
    if 'screen_name' in dbp:
        userName = dbp['screen_name']
    else:
        userName = session['username']
    return save_userlikes(data,userName)

'''
User dislikes is saved into database
'''
@app.route('/dislikes', methods=['POST'])
def post_usersdislikes():
    data = request.get_json(True)
    if 'screen_name' in dbp:
        userName = dbp['screen_name']
    else:
        userName = session['username']

    return save_usersdislikes(data,userName)


'''
Prime recommend the latest news, old news can be accessed  with the help 
of search feature.
'''
@app.route("/search",methods=['POST'])
def search():
    data = request.get_json(True)
    if 'screen_name' in dbp:
        userName = dbp['screen_name']
    else:
        userName = session['username']
    return searchNews(data,userName)

'''
User personalised intrest is saved into database and can be viewed 
from category page (personalised intrest page)
'''
@app.route('/category')
def category():
    #global POST_USERNAME
    if 'screen_name' in dbp:
        # login as a tweeter user
        userName = dbp['screen_name']
        app.logger.info("dbp['screen_name'] =" + dbp['screen_name'])
    else:
        # login as normal user
        userName = session['username']
        app.logger.info("session['username'] =" + session['username'])
    # transfer user's interest items to the web page 
    return render_template("category.html", user2category = get_perCategory(userName))


'''
Any updation in personalised page will be updated in database 
and can be used to prioriize recommended news category.
'''
@app.route('/category_modify', methods=['GET', 'POST'])
def category_modify():
    # get user's interests via the post
    pcid = request.form.get('ids')
    userName = ''
    if 'screen_name' in dbp:
        # login as a tweeter user
        userName = dbp['screen_name']
        app.logger.info("category_modify - dbp['screen_name'] =" + dbp['screen_name'])
    else:
        # login as a nomral user
        userName = session['username']
        app.logger.info("category_modify - session['username'] =" + session['username'])
    # update the user's interests into MongoDB
    update_perCategory(pcid,userName)   
    return render_template("user2category_saved.html")

'''
Search page will be loded inside the home page by replacing 
other page
'''
@app.route('/searchpage')
def searchpage():
    return render_template("Search.html")

'''
Saved article page will be loded inside the home page by replacing
other page
'''
@app.route('/saved')
def saved():
    return render_template("saved.html")


'''
App host and port is initialised (localhost ip can not be visible outside)
To make public, replace host by (0.0.0.0) and can use http port 80 or https port 443
'''
if __name__ == '__main__':
    # add log function for web app
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1) 
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.secret_key = 'mysecret'
app.run(host='127.0.0.1', debug=True, port=5000, threaded=True)