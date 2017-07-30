from flask import Flask, render_template, url_for, request, session, redirect, jsonify
from flask_cors import CORS
import bcrypt
#new imports

from bbcmodel import bbc_train, multidbfit,count_vect,tfidf_transformer
import tweepy #https://github.com/tweepy/tweepy
import pymongo
from bson.json_util import dumps, ObjectId
from sklearn.feature_extraction import text

from nltk.tokenize import TweetTokenizer
import pandas as pd
import os.path
import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
import gensim
from gensim import corpora



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
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = POST_USERNAME,count=200)
    
    #save most recent tweets
    alltweets.extend(new_tweets)
    

    #Liked Tweets
    likes_list = []
    for like in tweepy.Cursor(api.favorites,screen_name = POST_USERNAME,count=10).items(): #https://stackoverflow.com/questions/42420900/how-to-get-all-liked-tweets-by-a-user-using-twitter-api
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

    list1 = []
    list2 = []
    result = db.twtt.find({'screen_name' : POST_USERNAME})
    #s = ""
    for obj in result:
        s = ""
        list1.append(obj['text'])
        s = obj['text']

        tknzr = TweetTokenizer(strip_handles=True, reduce_len=True)
        l1 = tknzr.tokenize(s.lower())

        #Removing stop words
        l1 = [word for word in l1 if word not in stopwords]

        r = re.compile("http.*")
        new_list = filter(r.match, l1)  #http links
        for i in list(new_list):
            l1.remove(i)

        r = re.compile("#.*")
        new_list = filter(r.match, l1)

        hashtags_list = [x[1:] for x in new_list if x in l1]  # list contating hash words without hash symbol
        without_hashtags_list = [s for s in l1 if "#" not in s] #word without hashtag

        cleaned_tweet  =  hashtags_list + without_hashtags_list
        stringss = " ".join(cleaned_tweet)
        new = re.sub(r'[^A-Za-z]', ' ', stringss)
        new = new.split()

        #selfmade dictionary for removing some words
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


    #Spcay Replacing LDA
    import spacy

    document = ""
    for i in final_doc_list2:
        document = document + " " + i
    #define some parameters  
    nlp = spacy.load("en")

    document = nlp(document)
    print(type(document))

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
    cool = Counter(cleaned_list) .most_common(15)

    spacy_list = []
    spacy_var = [tup[0] for tup in cool]
    for i in spacy_var:
        spacy_list.append(re.sub(r'[^A-Za-z]', '', i))
    spacy_list = list(set(spacy_list))
    print(spacy_list)    




























    # #LDA
    # texts = list2
    # # turn our tokenized documents into a id <-> term dictionary
    # dictionary = corpora.Dictionary(texts)
    # # convert tokenized documents into a document-term matrix
    # corpus = [dictionary.doc2bow(text) for text in texts]

    # # generate LDA model
    # ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=50, id2word = dictionary, passes=10)
    # cool = ldamodel.print_topics(num_topics=50, num_words=1)

    # lda_list = []
    # lda = [tup[1] for tup in cool]
    # for i in lda:
    #     lda_list.append(re.sub(r'[^A-Za-z]', '', i))
    # lda_list = list(set(lda_list))
    # print(lda_list)

    #save LDA topics
    if db.spacytopics.find_one({'user':POST_USERNAME}) == None: # prevent duplicate tweets being stored
        db.spacytopics.save({ 'user' : POST_USERNAME,'topics' : spacy_list})
    else:
        db.spacytopics.update_one({'user': POST_USERNAME},{'$set':{'topics' : spacy_list}})


    #Classification using BBC
    category_list = []
    docs_new = final_doc_list2
    X_new_counts = count_vect.transform(docs_new)
    X_new_tfidf =  tfidf_transformer.transform(X_new_counts)
    predicted = multidbfit.predict(X_new_tfidf)

    for doc, category in zip(docs_new, predicted):
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

    document_writing_list_combined = final_category_list + spacy_list + hashtags_list#+ top_features
    
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

    interest_result = db.ldatopics.find({'user' : POST_USERNAME})
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
    
##########################################################################################################################
                                #For future use and ordering#
    #to save articles back to the db
    if "display_coll" in db.collection_names():
        db.display_coll.drop()
        db.display_coll.insert_many(list5)
    else:
        db.display_coll.insert_many(list5)

#ordering and displaying
    hybrid = db.display_coll.find().sort("publishedAt", -1 )
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
    app.run(host='127.0.0.1', debug=True, port=5000)
