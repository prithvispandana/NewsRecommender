from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from sqlalchemy.orm import sessionmaker
from tabledef import *

import tweepy #https://github.com/tweepy/tweepy
import csv
import pymongo

#import pymongo
#import nltk
from sklearn.feature_extraction.text import CountVectorizer
import nltk

#Twitter API credentials
consumer_key = "dWUQupK3yWLLAXReEKPUMLlwd"
consumer_secret = "985JhwgsTdzAgGBu6A6I2bTcgEVtLmKq23LMjrWRRrYNyOlf9s"
access_key = "90865238-Zon9cVIb8y3Ai6Qxv1t554kCQPDJr70M4haRrP6be"
access_secret = "eiAiw2xTlDeWzj4uazKWbKaKTAEOXFLw2FBHBsfFchMEJ"

engine = create_engine('sqlite:///tutorial.db', echo=True)
 
app = Flask(__name__)

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('afterlogin.html')#"Hello Boss!  <a href='/logout'>Logout</a>"
 
@app.route('/login', methods=['POST'])
def do_admin_login():
 
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])
 
    Session = sessionmaker(bind=engine)
    s = Session()
    query = s.query(User).filter(User.username.in_([POST_USERNAME]), User.password.in_([POST_PASSWORD]) )
    result = query.first()
    if result:
        session['logged_in'] = True
    else:
        flash('wrong password!')
    return home()
 
@app.route('/afterlogin', methods=['POST'])
def get_all_tweets():
    POST_USERNAME = str(request.form['username'])
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
    oldest = alltweets[-1].id - 1
    
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
    outtweets = [[tweet.id_str, tweet.created_at, tweet.text.encode("utf-8")] for tweet in alltweets]
    

    # Mongo initialization
    client = pymongo.MongoClient("localhost", 27017)
    db = client.tweets_db
    for s in alltweets:
        if db.twtt.find_one({'text':s.text}) == None: # prevent duplicate tweets being stored
            twtt = {'text':s.text, 'id':s.id, 'created_at':s.created_at,'screen_name':s.author.screen_name,'author_id':s.author.id}
            #print("THE TYPE IS :",type(i))
            db.twtt.insert_one(twtt)


    #write the csv  
    with open('%s_tweets.csv' % POST_USERNAME, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(["id","created_at","text"])
        writer.writerows(outtweets)
    
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
    top_n = 10
    top_features = [features[i] for i in indices[:top_n]]
    #print (top_features)
    #print(finallist)
    #for j in list2:
    #   print(j)
    db.keyword.save({ POST_USERNAME: top_features})


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
        print('%r => %s' % (doc, twenty_train.target_names[category]))
    category_list = list(set(category_list))
    db.interest.save({ POST_USERNAME: category_list})
    #try:
    #    #print("Hello there ----------------------------------------------------------------------")
    #    statuses = api.list_timeline(api.me().screen_name,screen_name = POST_USERNAME,count=200)
    #    print("Hello there ----------------------------------------------------------------------")
    #    for s in statuses:
    #        if db.twtt.find_one({'text':s.text}) == None: # prevent duplicate tweets being stored
    #            twtt = {'text':s.text, 'id':s.id, 'created_at':s.created_at,'screen_name':s.author.screen_name,'author_id':s.author.id}
    #            db.twtt.save(twtt)
    #    #print("Hello there ----------------------------------------------------------------------")
    #except tweepy.error.TweepError:
    #    print ("Whoops, could not fetch tweets!")
    #except UnicodeEncodeError:
    #    pass

    return 'success'


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()
 
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
