from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_cors import CORS
import bcrypt
import pickle
#new imports

import tweepy #https://github.com/tweepy/tweepy
import pymongo
from bson.json_util import dumps, ObjectId
from sklearn.feature_extraction import text

import pandas as pd
import os.path
import spacy
import re

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
with open('bbcmodel.pkl', 'rb') as fin:
        vectorizer, clf, bbc_train = pickle.load(fin)


@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    elif dbp:
        return render_template('landing.html', user =dbp['screen_name'] , img_url=dbp['prof_url'])
    else:
        return render_template('landing.html')


@app.route('/login')
def twitterlogin():
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET, CALLBACK_URL)    
    try: 
        #get the request tokens
        redirect_url= auth.get_authorization_url()
        session['request_token']= (auth.request_token)
    except tweepy.TweepError:
        print('Error! Failed to get request token')
    
    #this is twitter's url for authentication
    return redirect(redirect_url)

@app.route("/logout")
def logout():
    session['logged_in'] = False
    dbp.clear()
    return index()

@app.route("/verify")
def get_verification():
    
    #get the verifier key from the request url
    verifier= request.args['oauth_verifier']
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    token = session['request_token']
    del session['request_token']
    auth.request_token=token
    try:
        verifier = request.args.get('oauth_verifier')
        auth.get_access_token(verifier)
        session['token'] = (auth.access_token, auth.access_token_secret)
    except tweepy.TweepError:
            print('Error! Failed to get access token.')
    
    #now you have access!
    api = tweepy.API(auth)
    session['logged_in'] = True
    #store in a db
    dbp['api']=api
    dbp['access_token_key']=auth.access_token
    dbp['access_token_secret']=auth.access_token_secret
    
    return redirect(url_for('authorized'))

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
#    print(api.get_user('screen_name'))
#    POST_USERNAME = api.get_user('screen_name')
        return render_template('landing.html', user=POST_USERNAME, img_url=img)


@app.route("/home")
def home():
    return render_template("home.html")

@app.route('/recom', methods=['GET', 'POST'])
def get_all_tweets():
#     #Mongo initialization
#     client = pymongo.MongoClient("localhost", 27017)
#     db = client.tweets_db
    try:      
        api = dbp['api']
    except Exception as e:
        gen_user = db.news.find().sort("publishedAt", -1 ).limit(10)
        return dumps(gen_user)
        
        
    #initialize a list to hold all the tweepy Tweets
    new_tweets = api.user_timeline(screen_name = POST_USERNAME,count=200, tweet_mode="extended")
    tweets = [" ".join([tweet.full_text]) for tweet in new_tweets]

    

    likes_tweets=api.favorites(screen_name = POST_USERNAME,count=10,tweet_mode="extended")
    liked = [" ".join([like.full_text]) for like in likes_tweets]
    tweets.extend(liked)

    
    document=" ".join(tweets)
    document = nlp(document)

    all_tags = {w.pos: w.pos_ for w in document}

    noisy_pos_tags = ['PROP']
    min_token_length = 2

    #Function to check if the token is a noise or not  
    def isNoise(token):     
        is_noise = False
        if token.pos_ in noisy_pos_tags:
            is_noise = True 
        elif token.is_stop == True:
            is_noise = True
        elif len(token.string) <= min_token_length:
            is_noise = True
        return is_noise 
    def cleanup(token, lower = True):
        if lower:
            token = token.lower()
        return token.strip()

    # top unigrams used in the reviews 
    from collections import Counter
    cleaned_list = [cleanup(word.string) for word in document if not isNoise(word)]
    cool = Counter(cleaned_list) .most_common(30)
    spacy_list = []
    spacy_var = [tup[0] for tup in cool]
    for i in spacy_var:
        spacy_list.append(re.sub(r'[^A-Za-z]', '', i))
    labels = set([w.label_ for w in document.ents])
    for label in labels: 
        entities = [cleanup(e.string, lower=False) for e in document.ents if label==e.label_] 
        spacy_list.extend(entities)
        print(label,str(entities))
    
    #print("",spacy_list) 
    processedWords=list(set(spacy_list))

    if db.spacytopics.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.spacytopics.save({ 'user' : POST_USERNAME,'topics' : processedWords})
    else:
        db.spacytopics.update_one({'user': POST_USERNAME},{'$set':{'topics' : processedWords}})


    category_list = []
    X_new = vectorizer.transform(processedWords)
    X_new_preds = clf.predict(X_new)
    for doc ,category in zip(processedWords, X_new_preds):
        category_list.append(bbc_train.target_names[category])
        #print('%r => %s' % (doc, twenty_train.target_names[category]))
    
    final_category_list = []
    counts = dict()
    for i in category_list:
        counts[i] = counts.get(i, 0) + 1
        if i == 'tech':
            final_category_list.append("technology")
        else:
            final_category_list.append(i)



    ######################################################################################################
    #NEW PART
    print(counts)

    #To change dict key name from tech to technology
    if 'technology' in counts.keys():
        counts['technology'] = counts.pop('tech')

    #Putting default value of 0 for categories not present in the classification result
    c_list = ['business','entertainment','politics','sport','technology']
    for i in c_list:
        if i not in list(counts.keys()):
            counts[i] = 0
    
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

    document_writing_list_combined = final_category_list + processedWords #+ hashtags_list#+ top_features
    
    save_path = R'files'   
    completeName = os.path.join(save_path, POST_USERNAME)         
    file1 = open(completeName, "w",encoding='utf8')
    for i in document_writing_list_combined:
        file1.write(i+'\n')
    file1.close()


#######################################################################################################################
                                    #Collaborative filtering#
    topN=2
    uniset=set()
    for top in getTopN(POST_USERNAME, topN):
        fileName = os.path.join(save_path, top) 
        if not fileName:
            continue
        else:
            uniset.update(set(open(fileName).read().split())) 
        
    #substract from original
    result_set=set()  #unique set of similar user
    if uniset:
        fileName = os.path.join(save_path, POST_USERNAME)
        origin=set(open(fileName).read().split())
        result_set=origin-uniset

#######################################################################################################################

    res=[]
    interest_result = db.spacytopics.find({'user' : POST_USERNAME})
    for obj in interest_result:
        res = obj['topics']


#######################################################################################################################
                                    #news based on profile interest
    list4 = []
    for i in res:
        if db.news.find({'keywords' : i}) != None:
            resultset = db.news.find({'keywords' : i})
        for k in resultset:
            list4.append(k)
        else:
            continue

########################################################################################################################  
                                            #similar user interest#
    for i in result_set:
        if db.news.find({'keywords' : i}) != None:
            resultset = db.news.find({'keywords' : i})
            for k in resultset:
                list4.append(k)
            else:
                continue
            
            
    list5 = [i for n, i in enumerate(list4) if i not in list4[n + 1:]]
    # d_inter = dict([k, v for k, v in dict1.iteritems() if k in dict2 and dict2[k] == v])
    

##########################################################################################################################


#Adding the category_score parameter to each news article document and then inserting into the collection for ordering  purposes
    list_technology=[]
    list_business=[]
    list_politics=[]
    list_sport=[]
    list_entertainment=[]
    list_gaming=[]
    list_general=[]
    list_music=[]
    list_science_and_nature=[]



    for i in list5:
        if i['category'] == "technology":
            i['category_score'] = counts['technology']
            list_technology.append(i)
        if i['category'] == "business":
            i['category_score'] = counts['business']
            list_business.append(i)
        if i['category'] == "politics":
            i['category_score'] = counts['politics']
            list_politics.append(i)
        if i['category'] == "sport":
            i['category_score'] = counts['sport']
            list_sport.append(i)
        if i['category'] == "entertainment":
            i['category_score'] = counts['entertainment']
            list_entertainment.append(i)
        if i['category'] == "gaming":
            list_gaming.append(i)
        if i['category'] == "general":
            list_general.append(i)
        if i['category'] == "music":
            list_music.append(i)
        if i['category'] == "science-and-nature":
            list_science_and_nature.append(i)

    list5 = list_technology[:20] + list_business[:20] +list_politics[:20]+ list_sport[:20]+ list_entertainment[:20]+list_gaming[:20]+list_general[:20]+list_music[:20]+list_science_and_nature[:20]
    #For future use and ordering#
    #to save articles back to the db
    if POST_USERNAME in db.collection_names():
        db[POST_USERNAME].drop()
        db[POST_USERNAME].insert_many(list5)
    else:
        db[POST_USERNAME].insert_many(list5)

#ordering and displaying ( ordering on category and published time)
    hybrid =  db[POST_USERNAME].find().sort([["category_score",pymongo.DESCENDING],["publishedAt",pymongo.DESCENDING]] )


    # title_text=[]
    # for obj in hybrid:
    #     if obj["title"] = 
    #     title_text.append(obj['title'])

    print(type(hybrid))
    #hybrid.limit(30)
    return dumps(hybrid)

#############################################################################################################################
#---------------------------------------
# Generate top 5 similar news for each recommended news
#---------------------------------------
@app.route('/simNews', methods=['POST'])
def simNews():
    #retrieve the object to find the similar news of it
    data = request.get_json(True)
    
    # get excluded URLs that should not show up in embmed documents
    excURLs = getExcludedURL(data)
    strCategory =data['category']
    strSearch = data['title'] + " " + data['description']
     
    #search the data in database    
    cursor = db.news.find({'url': { '$nin': excURLs}, \
                                    'category': strCategory,    \
                                    '$text': { '$search': strSearch, '$caseSensitive': False, '$diacriticSensitive': False, '$language': 'en'}},\
                                   { 'score': { '$meta': 'textScore' }})
    # sort by score and published date
    cursor.sort([('score', {'$meta': 'textScore'}),('publishedAt', pymongo.DESCENDING)])
    
    # have the top 9 docuemnts
    cursor.limit(9)                      
    return dumps(cursor)


def getExcludedURL(jsonData):
    urlList = []
    urlList.append(jsonData['url'])
    #only one article thats why code commented
#     for i in list:
#         urlList.append(i['url'])
    return urlList

#####################################################################################################################
#Method to find similar user
def getTopN(user, topN): 
    try:
        topUsers=[]
        #load the similarity matrix
        cursor = db["sim_col"].find({},{"_id":0})
        # Expand the cursor and construct the DataFrame
        df =  pd.DataFrame(list(cursor))
          
        if not df.empty:
            #load the all list of user ordered
            cursor1=db["list_user"].find({},{"_id":0})
            
            #build the list
            user_name=list(cursor1)
            for a in user_name:
                list_user=a['index']
                
            #To update the dataframe load in new to avoid NAN value
            adf = pd.DataFrame(data=df)
            #index updated
            adf.index=list_user
            #convert into dictionary
            access_df=adf.to_dict()
            topUsers=sorted(access_df[user], key=access_df[user].get, reverse=True)[1:topN+1]
    except Exception as e:
        print(e)
        return topUsers
    return topUsers

########################################################################################################

#----------added by Bo (start) 20170724 --------
@app.route('/category')
def category():
    #global POST_USERNAME
    if 'screen_name' in dbp:
        userName = ['screen_name']
    else:
        userName = session['username']
    result = db.user2category.find({'userName' : userName},{'categories':1, '_id':0})
    x = []
    for i in result:
        x.append(i)
    print(x)
    if x == []:
        user2categoryLst = []
    else:
        user2categoryLst = x[0]["categories"]
    return render_template("category.html", user2category = user2categoryLst)

@app.route('/category_modify', methods=['GET', 'POST'])
def category_modify():
    ids = request.form.get('ids')
    lst = []
    if ids is not None:
        lst = ids.split(',')
        
    if 'screen_name' in dbp:
        userName = ['screen_name']
    else:
        userName = session['username']
    db.user2category.update_one({'userName' : userName}, {'$set':{'categories': lst}}, upsert=True)
    return render_template("user2category_saved.html")
#----------added by Bo (end) 20170724 --------


#-----------------------Prithvi- 29/07/2017----------------------------------------------
@app.route('/usernews', methods=['POST'])
def post_usernews():
    print("Hello")
    data = request.get_json(True)
    print(data)
    print(data['newsId'])
    print(data['userId'])
    ans=db.usernews.find_one({'newsId':data['newsId'],'userId':data['userId']})
    print(ans)
    if ans==None:
        print('Document not found.Ready to insert')
        ans = db.usernews.insert_one(data)
        print('Document Inserted')
    else:
        print("Document Already exists")

    return jsonify({ "status": "ok"})

    # return jsonify({ "status": "ok"})

@app.route('/usernews/<userid>', methods=['GET'])
def get_usernews(userid):
    # get from db db.usernews
    print(userid)
    news = db.usernews.find({ "userId": userid})
    #print(news)
    articles = []
    for obj in news:
        print(obj['newsId'])
        #x=obj['newsId']
        art = db.news.find_one( ObjectId(obj['newsId'] ))
        articles.append(art)
    print(articles)
    return dumps(articles)


@app.route('/likes', methods=['POST'])
def post_userlikes():

    data = request.get_json(True)
    print(data)
    ans = db.userslikes.find_one({'newsId': data['newsId'], 'userId': data['userId']})
    if ans == None:
        print('Document not found.Ready to insert')
        ans = db.userslikes.insert_one(data)
        print('Document inserted')
    else:
        print("Document Already exists")
    return jsonify({ "status": "ok"})

@app.route('/dislikes', methods=['POST'])
def post_usersdislikes():
    data = request.get_json(True)
    print(data)
    ans = db.usersdislikes.find_one({'newsId': data['newsId'], 'userId': data['userId']})
    if ans == None:
        print('Document not found.Ready to insert')
        ans = db.usersdislikes.insert_one(data)
        print('Document inserted')
    else:
        print("Document Already exists")
    return jsonify({ "status": "ok"})

@app.route('/saved')
def saved():
    return render_template("saved.html")


#--------------------------------------------------------------------------------

#up flask mongo server
if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(host='127.0.0.1', debug=True, port=5000, threaded=True)


    # db.news.find(ObjectId("597db45f73714e21d84f2cf2"))
    #  db.HardmanGunner.find("title":"United States", "title" : "'War for the Planet of the Apes' wins a quiet weekend at the box office")