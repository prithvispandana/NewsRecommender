from flask import Flask, request, redirect, url_for, session, g, flash, \
     render_template
from flask_oauthlib.client import OAuth
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
 


from flask import Flask, render_template, url_for, request, session, redirect
#from flask.ext.pymongo 
import pymongo
import bcrypt

#new imports
from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os


import tweepy #https://github.com/tweepy/tweepy
import csv
import pymongo

from sklearn.feature_extraction.text import CountVectorizer
import nltk 
# configuration
SECRET_KEY = 'development key'
DEBUG = True
 
# setup flask
app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY
oauth = OAuth()

#Twitter API credentials
consumer_key = "dWUQupK3yWLLAXReEKPUMLlwd"
consumer_secret = "985JhwgsTdzAgGBu6A6I2bTcgEVtLmKq23LMjrWRRrYNyOlf9s"
access_key = "90865238-Zon9cVIb8y3Ai6Qxv1t554kCQPDJr70M4haRrP6be"
access_secret = "eiAiw2xTlDeWzj4uazKWbKaKTAEOXFLw2FBHBsfFchMEJ"
 
# Use Twitter as example remote application
twitter = oauth.remote_app('twitter',
   #consumer_key='xBeXxg9lyElUgwZT6AZ0A',
    #consumer_secret='aawnSpNTOVuDCjx7HMh6uSXetjNN8zWLpZwCEU4LBrk',
    consumer_key='SkaYjiRh8xSeiJdgodBxpbRGZ',
    consumer_secret='ihP1T7lIFEyT3UkX6niqAKdoS1fot8kNamnKNx8s3XUdvHKyLv',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authorize'
)
 
app.config['MONGO_DBNAME'] = 'mongologinexample'
app.config['MONGO_URI'] = 'mongodb://pretty:printed@ds021731.mlab.com:21731/mongologinexample'

#mongo = PyMongo(app)

client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db 


@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')
 
@app.route('/')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))
 
    access_token = access_token[0]
 
    return render_template('index.html')
 
@app.route('/login')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/loginapp', methods=['POST'])  
def loginapp():
    #users = mongo.db.users
    login_user = db.users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            session['logged_in'] = True
            return "loggedin"

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
 
@app.route('/logout')
def logout():
    session.pop('screen_name', None)
    flash('You were signed out')
    return redirect(request.referrer or url_for('index'))
 
 
@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)
 
    access_token = resp['oauth_token']
    session['access_token'] = access_token
    session['screen_name'] = resp['screen_name']
    POST_USERNAME = session['screen_name']
    session['twitter_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    
    #POST_USERNAME = str(request.form['username'])
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
    
    #save the id of the oldest tweet less one
    #oldest = alltweets[-1].id - 1
    
    #keep grabbing tweets until there are no tweets left to grab
    #while len(new_tweets) > 0:
    #    print ("getting tweets before %s" % (oldest))
    #    
    #    #all subsiquent requests use the max_id param to prevent duplicates
    #    new_tweets = api.user_timeline(screen_name = POST_USERNAME,count=200,max_id=oldest)
    #    
    #    #save most recent tweets
    #    alltweets.extend(new_tweets)
    #    
    #    #update the id of the oldest tweet less one
    #    oldest = alltweets[-1].id - 1
    #    
    #    print ("...%s tweets downloaded so far" % (len(alltweets)))
    # 
    #transform the tweepy tweets into a 2D array that will populate the csv 
    #outtweets = [[tweet.id_str, tweet.created_at, tweet.text.encode("utf-8")] for tweet in alltweets]
    

    # Mongo initialization
    client = pymongo.MongoClient("localhost", 27017)
    db = client.tweets_db
    for s in alltweets:
        if db.twtt.find_one({'text':s.text}) == None: # prevent duplicate tweets being stored
            twtt = {'text':s.text, 'id':s.id, 'created_at':s.created_at,'screen_name':s.author.screen_name,'author_id':s.author.id}
            #print("THE TYPE IS :",type(i))
            db.twtt.insert_one(twtt)


    #write the csv  
    # with open('%s_tweets.csv' % POST_USERNAME, 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["id","created_at","text"])
    #     writer.writerows(outtweets)
    
    pass

    from sklearn.feature_extraction import text
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
    #print(s)
    #tokenize = CountVectorizer().build_tokenizer()
    #finallist = []
    #for i in s.split():
        
    # convert to lowercase, then tokenize
        tokens1 = tokenize(s.lower())
        
    #Stop word list
    #from sklearn.feature_extraction import text
    #stopwords = text.ENGLISH_STOP_WORDS

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

    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

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

    from sklearn.datasets import fetch_20newsgroups
    twenty_train = fetch_20newsgroups(subset='train',categories=categories, shuffle=True, random_state=42)

    count_vect = CountVectorizer()
    X_train_counts = count_vect.fit_transform(twenty_train.data)
    #print(X_train_counts.shape)

    from sklearn.feature_extraction.text import TfidfTransformer
    tf_transformer = TfidfTransformer(use_idf=False).fit(X_train_counts)
    X_train_tf = tf_transformer.transform(X_train_counts)
    #print(X_train_tf.shape)


    tfidf_transformer = TfidfTransformer()
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    #print(X_train_tfidf.shape)


    from sklearn.naive_bayes import MultinomialNB
    clf = MultinomialNB().fit(X_train_tfidf, twenty_train.target)

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
        if i == 'talk.politics.misc':
            final_category_list.append("business")
        elif i == 'sci.electronics':
            final_category_list.append('electronics')
        elif i == 'comp.graphics':
            final_category_list.append('gaming')
        elif i == 'misc.forsale':
            final_category_list.append('general')
        elif i == 'talk.politics.guns' or i == 'talk.politics.mideast':
            final_category_list.append('politics')
        elif i == 'sci.crypt' or i == 'sci.space' or i == 'sci.med':
            final_category_list.append('science-and-nature')
        elif i == 'rec.autos' or i == 'rec.sport.baseball' or i == 'rec.sport.hockey':
            final_category_list.append('sport')   
        elif i == 'comp.windows.x' or i == 'comp.sys.mac.hardware':
            final_category_list.append('technology')

        #pass
    final_category_list = list(set((final_category_list)))    
    if db.interest.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.interest.save({ 'user' : POST_USERNAME,'interest' : final_category_list})
    else:
        db.interest.update_one({'user': POST_USERNAME},{'$set':{'interest' : final_category_list}})



    document_writing_list_combined = final_category_list + top_features

    #User document
    # file = open(POST_USERNAME,'w',encoding='utf8') 
    # for i in document_writing_list_combined:
    #     file.write(i+'\n')

    # file.close()

    # import os

    # filepath = os.path.join(R'C:\Users\harshdev\Desktop\flaskmongo\files', POST_USERNAME) #https://docs.python.org/2/reference/lexical_analysis.html#string-literals
    # if not os.path.exists(R'C:\Users\harshdev\Desktop\flaskmongo\files'):
    #     os.makedirs(R'C:\Users\harshdev\Desktop\flaskmongo\files')
    # f = open(POST_USERNAME, "w",encoding='utf8')
    # for i in document_writing_list_combined:
    #     f.write(i+'\n')

    # f.close()


    import os.path
    save_path = R'C:\Users\harshdev\Desktop\finaltese\files'   
    completeName = os.path.join(save_path, POST_USERNAME+".txt")         
    file1 = open(completeName, "w",encoding='utf8')
    for i in document_writing_list_combined:
        file1.write(i+'\n')
    file1.close()

###############################################################################################################3333

    import glob #find the all path names with matching a specified pattern
    import os
    import nltk
    import re
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity


    #each profile is stored in one document either in local or database
    #document name must be profile_id
    all_profiles=[] #List is created to store all profiles
    profiles_id=[]
    for filename in glob.glob('files/*'): #include all the files from current directory
        fin = open(filename,"r")  #open the file for reading
        profiles_id.append(os.path.basename(filename)) #document name for future reference
        all_profiles.append(fin.read()) #read full content of file and added to the client
        fin.close() #close the file
    print("Number of profiles %d" % len(all_profiles)) #Total number of profiles



    # from sklearn.feature_extraction.text import CountVectorizer
    # # define the function for lemmatization
    # def lemma_tokenizer(text):
    #     # use the standard scikit-learn tokenizer first
    #     standard_tokenizer = CountVectorizer().build_tokenizer()
    #     tokens = standard_tokenizer(text)
    #     # then use NLTK to perform lemmatisation on each token
    #     lemmatizer = nltk.stem.WordNetLemmatizer()
    #     lemma_tokens=[]
    #     for token in tokens:
    #         if re.search('[a-zA-Z]', token):  # save those which are non-numeric
    #             lemma_tokens.append(lemmatizer.lemmatize(token))
    #     return lemma_tokens


    # we can pass in the same preprocessing parameters
    tf_idfVector = TfidfVectorizer(stop_words="english",min_df =1,ngram_range=(1,1))#chosen n-gram of three words. It will produce phrases containing upto three words
    tf_idfMatrix= tf_idfVector.fit_transform(all_profiles)
    #
    #print(tf_idfMatrix)
    cosSim=cosine_similarity(tf_idfMatrix)
    #print(cosSim)
    df = pd.DataFrame(cosSim,columns=profiles_id,index=profiles_id)
    #df = pd.DataFrame(cosSim,columns
                      #w=profiles_id)

    print()
    dic = df.to_dict()
    #print(df.to_dict())
    print('----------------------------')
    print(dic)
    print()
    print('----------------------------')
    # print(dic['110273156'])
    # print( df.groupby('110273').head(2))
    print()
    print()


    def call(user, no):
        # print(type(user))
        
        userlist = []
        keys = dic[str(user)].keys()
        print(keys)
        lst = []
        for each in keys:
            if (dic[str(user)].get(each) < 1.0):
                lst.append(dic[str(user)].get(each))

        print()
        print("-------sorted-------")
        print()
        lst2 = []
        lst2 = sorted(lst , reverse=True)
        print(lst2)
        print()

        for each in keys:
            for index, item in enumerate(lst2):
                if (index <= no):

                    if (dic[str(user)].get(each) == lst2[index]):
                        userlist.append(each)
        return userlist
        

    # gets top 2 users (0 and 1 from the list)
    result = call(POST_USERNAME+".txt", 1)
    print("-------RESULT-------------")
    print()
    print(result)

    usrlist=[]
    interest = []
    for r in result:
        for filename in glob.glob('files/'+str(r)):
            fin = open(filename, 'r')
            
            lines = fin.readlines()
            for l in lines:
                print( l.strip() )
                usrlist.append(l.strip())
        
        for filename in glob.glob('files/'+str(POST_USERNAME+".txt")):
            fin = open(filename, 'r')
            
            lines = fin.readlines()
            for l in lines:
                interest.append(l.strip())
        
    print("------suggestion topics from similar users-----")
    print(usrlist)
    print(interest)
    print(set(usrlist) - set(interest))
######################################################################################################################################




    interest_result = db.interest.find({'user' : POST_USERNAME})
    for obj in interest_result:
        res = obj['interest']

    list4 = []
    for i in res:
        if db.news.find({'cagtegory' : i}) != None:
            resultset = db.news.find({'cagtegory' : i})
            for k in resultset:
                list4.append(k)
                #print(k['title'])
        else:
            continue

    return render_template('outputscreen.html',output = list4)
    return "done"
 
    #return redirect(url_for('index'))
 
 
if __name__ == '__main__':
    app.run()