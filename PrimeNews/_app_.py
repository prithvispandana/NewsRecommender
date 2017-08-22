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
db = client.tweets_db #DB is created if not exist in mongodb
nlp = spacy.load("en") #loan the spacy model to detect english keywords
topN=2

'''
This method listen all the request which starts with forward slash(/)
if user is already logged in system , then user will redirect to home 
(recommendation article page)otherwise user will redirect to index(login page)
'''
@app.route('/')
def index():
    if not session.get('logged_in'): #if user is not logged in 
        dbp.clear()
        return render_template('index.html') #redirected to login page of application
    elif dbp: #If user is twitter user
        return render_template('landing.html', user =dbp['screen_name'] , img_url=dbp['prof_url']) #home page is loaded
    else:
        dbp.clear()
        return render_template('landing.html', user=session['username']) #home page for non twitter user


'''
This method register the user who doesn't have twitter aaccount can 
register with prime application but this kind of user only get top 
stories and prime appliaction run over time and recommend the news accordingly.
'''
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        #Non twitter users
        existing_user = db.users.find_one({'name' : request.form['username']}) #search the user is exist or not in database

        if existing_user is None: #if user is not exist then register the user
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt()) #password is encrypted
            db.users.insert({'name' : request.form['username'], 'password' : hashpass}) #encrypted password is stored in database
            session['username'] = request.form['username'] #user name from screen
            return redirect(url_for('index')) #redirection to login page
        return 'That username already exists!' #if user exist throw the error
    return render_template('register.html')


'''
Non twitter users logins to system and validate the user login id 
and password from the databse
'''
@app.route('/login', methods=['POST'])  
def login():
    login_user = db.users.find_one({'name' : request.form['username']}) #check user is present in database or not
    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']: #password matching
            session['username'] = request.form['username'] #user name from screen
            session['logged_in'] = True #make the session true
            return redirect(url_for('index')) #redirect to index method which redirect page according to user type
    return 'Invalid username/password combination' #if not match error is shown


'''
Twitter user login to system, To do so user authorised the application 
for access of request token and redirect url from registered prime twitter 
application
'''
@app.route('/login')
def twitterlogin():
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK_URL)  #standard way to create auth object of application
    try: 
        #get the request tokens
        redirect_url= auth.get_authorization_url() #get authorized redirection url which is registered in twitter
        session['request_token']= (auth.request_token) #access the request token
    except tweepy.TweepError: #if error occur during access of token
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
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET) #auth object is created
    token = session['request_token'] #access token from session variable
    #del session['request_token']
    auth.request_token=token 
    try:
        verifier = request.args.get('oauth_verifier') #create user varifier object
        auth.get_access_token(verifier) #get access token of user
        session['token'] = (auth.access_token, auth.access_token_secret) #store user token
        dbp.clear() #clear previous entry
        api = tweepy.API(auth) #auth is updated for user and create api which can access the value
        session['logged_in'] = True #Make the session true
        #store in a db
        dbp['api']=api #store api for longer user
        dbp['access_token_key']=auth.access_token #auth access token of user
        dbp['access_token_secret']=auth.access_token_secret #auth secret token of user
    except tweepy.TweepError:
            print('Error! Failed to get access token.')    
    return redirect(url_for('authorized'))


'''
If user is already logged in system, then user will redirect to landing
(recommendation article page), otherwise user will redirect to index page
'''    
@app.route('/authorized')
def authorized():
    if not session.get('logged_in'): #if session is not true redirect to login page
        return render_template('index.html')
    else:
        global POST_USERNAME #store the user name in global variable
        api = dbp['api'] #access api of user from dictionary
        usr =api.me()
        POST_USERNAME=usr.screen_name #user screen name
        img=usr.profile_image_url #user profile url
        dbp['screen_name']=POST_USERNAME #store user name in dictionary for longer user
        dbp['prof_url']=img #store image
        dbp['acc_location']=usr.location #store location
        dbp['time_zone']=usr.time_zone #store time_zone
        return render_template('landing.html', user=POST_USERNAME, img_url=img) #redirect to home page of screen


'''
This method invalidate the user session and redirect to index (login page)
'''
@app.route("/logout")
def logout():
    #session["__invalidate__"] = True
    session.pop('logged_in', None) #make the session None
    #session['logged_in'] = False
    dbp.clear() #clear the dictionary
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
        gen_user = db.news.find().sort("publishedAt", -1 ).limit(180) #non twitter user recoomend the top stories in each category
        return dumps(gen_user)
    recom_scoredList=[]
    try:    
        friend_list=save_friendList(api,POST_USERNAME) #get the user friend list
        tweets = get_tweets(api, POST_USERNAME) #get user tweets
        liked = get_likes(api,POST_USERNAME) #get user likes
        tweets.extend(liked) #make single collection for likes, tweet and retweet
        document=" ".join(tweets) #convert list to string by space seprateor
        document = nlp(document) #Pass the string to spacy nlp function for pre processing
        most_common=get_mostCommon(document) #get most common keywords spacy
        entities=get_entities(document) #get user entities 
        most_common.extend(entities) #add entities to most common
        processedWords=list(set(most_common)) #make single unique list of all keywords
        save_uniqueWords(processedWords,POST_USERNAME) #save words in database
        tweet_intrest=get_tweetIntrest(tweets) #calculate user intrest from tweets
        final_intrest_category, normCounts = get_normIntrest(tweet_intrest) #counts dictionary of tweets
        final_intrest_category = list(set(final_intrest_category)) #make unique list of calculated category intrest
        save_tweetIntrest(final_intrest_category,POST_USERNAME) #user intrest is saved to database
        profile_list_combined = final_intrest_category + processedWords #combined list of catgory and processed words
        save_profile(profile_list_combined,POST_USERNAME) #user profile is saved
        result_set=get_collKeywords(topN,POST_USERNAME) #Similar user profile keywords is extracted
        app_likes=get_appLikes(POST_USERNAME) #user liked article keywords in prime application
        app_saved=get_appsaved(POST_USERNAME) #user saved article keywords list in prime application
        final_search_list = list(result_set) + processedWords + app_likes + app_saved #final list to search in database
        #cold start user
        if dbp['acc_location'] is not None and dbp['acc_location']!="": #update the search list, it helps in case of cold start user
            final_search_list.extend(dbp['acc_location'].split(","))
        if dbp['time_zone'] is not None and dbp['time_zone']!="":   #cold start user time zone
            final_search_list.extend(dbp['time_zone'].split(","))
        search_kwlst = set([ i.lower() for i in final_search_list]) #final keyword list which is searched in database
        recom_list = db.news.find({"keywords":{"$in": list(search_kwlst)}}) #database search query
        recom_scoredList=assign_score(recom_list, normCounts)
        if not recom_scoredList: #If cold start problem is not solved with location and timezone field give top stories
            recom_scoredList = db.news.find().sort("publishedAt", -1 ).limit(180) #top stories
    except Exception as e:
        print(e)
        return "Sorry We are not able to process your request this Time" #in case of exception 
    return dumps(recom_hybridarticles(recom_scoredList,POST_USERNAME))

'''
This method returns the article which are similar to the recommended article
'''
@app.route('/simNews', methods=['POST'])
def simNews():
    data = request.get_json(True) #get the title and description of user which is passed to similer news function
    # get similar news articles
    return sim_News(data)

'''
User article is saved and can be read in future fron saved article user interface
'''
@app.route('/usernews', methods=['POST'])
def post_usernews():
    data = request.get_json(True) #get iportant field of user news
    if 'screen_name' in dbp:
        userName = dbp['screen_name'] #twitter user
    else:
        userName = session['username'] #non twitter user

    return save_userNews(data,userName) #news article is saved along with username


'''
Saved article is accessed using userid
'''
@app.route('/usernews/<userid>', methods=['GET'])
def get_usernews(userid):
    return get_userNews(userid) #get saved news of user


'''
User likes saved into database as a explicit feedback and used 
for future recommendation.
'''
@app.route('/likes', methods=['POST'])
def post_userlikes():
    data = request.get_json(True) #get id and other details of news of userlikes
    print(data)
    if 'screen_name' in dbp:
        userName = dbp['screen_name'] #twitter user
    else:
        userName = session['username'] #non twitter user
    return save_userlikes(data,userName) #save user likes in database

'''
User dislikes is saved into database
'''
@app.route('/dislikes', methods=['POST'])
def post_usersdislikes():
    data = request.get_json(True) #user dislike article information
    if 'screen_name' in dbp:
        userName = dbp['screen_name']
    else:
        userName = session['username']

    return save_usersdislikes(data,userName) #save user dislike along with user name


'''
Prime recommend the latest news, old news can be accessed  with the help 
of search feature.
'''
@app.route("/search",methods=['POST'])
def search():
    data = request.get_json(True) #get the search field data
    if 'screen_name' in dbp:
        userName = dbp['screen_name']
    else:
        userName = session['username']
    return searchNews(data,userName) # return search news from database

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
