import spacy
import tweepy
import pandas as pd
import re
import pymongo
import pickle
import os
from collections import Counter


#Properties used in methods
noisy_pos_tags = ['PROP']
min_token_length = 2
common_token=30
save_path = R'files'
#Mongodb client
client = pymongo.MongoClient("localhost", 27017)
db = client.tweets_db

#load model for prediction
with open('primemodel.pkl', 'rb') as fin:
        vectorizer, clf, prime_train = pickle.load(fin)


'''
This method predict the user intrest with the help of user tweets, retweets likes
'''
def get_tweetIntrest(tweets):
    intrest_list = []
    X_new = vectorizer.transform(tweets)
    X_new_preds = clf.predict(X_new)
    for doc ,category in zip(tweets, X_new_preds):
        intrest_list.append(prime_train.target_names[category])
    return intrest_list

'''
Tweet intrest saved into databse for future recommendation use and also
for analysis purpose, how user intrest changed over time?
'''
def save_tweetIntrest(final_intrest_category,userName):
    if db.interest.find_one({'user':userName}) == None: # prevent duplicate tweets being stored
        db.interest.save({ 'user' : userName,'interest' : final_intrest_category})
    else:
        db.interest.update_one({'user': userName},{'$set':{'interest' : final_intrest_category}})


'''
standard way to validate spacy tokens
This method validate all the passed tokens and set true false on it
'''
def isNoisy(token):     
    is_noise = False
    if token.pos_ in noisy_pos_tags:
        is_noise = True 
    elif token.is_stop == True:
        is_noise = True
    elif len(token.string) <= min_token_length:
        is_noise = True
    return is_noise 

'''
This method converts token into lower case notation and returned stripped token
'''
def clean(token, lower = True):
    if lower:
        token = token.lower()
    return token.strip()

'''
This method return topN similar user 
'''
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

'''
This method calls the getTopN method and with the help of topN users
returns the unique keywords of colloborative filtering.
'''
def get_collKeywords(topN,userName):
    uniset=set()
    for top in getTopN(userName, topN):
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
    return result_set

'''
This method save all friends following to database and used in profile similarity
calculation
'''
def save_friendList(api,userName):
    friend_list = []
    for friend in tweepy.Cursor(api.friends,count=50).items(): 
        friend_list.append(friend.screen_name)
    if db.friends.find_one({'user':userName}) == None: # prevent duplicate tweets being stored
        db.friends.save({ 'user' : userName,'friendsList' : friend_list})
    else:
        db.friends.update_one({'user': userName},{'$set':{'friendsList' : friend_list}})  
    return friend_list   
   
'''
This method returns the 200 user tweets and call the save hastag method 
to save hashtag into database. These hashtag can be used in profile similarity
calculation
'''    
def get_tweets(api, userName):
    new_tweets = api.user_timeline(count=200, tweet_mode="extended")
    save_hashtag(new_tweets,userName)
    tweets = [" ".join([tweet.full_text]) for tweet in new_tweets]
    return tweets

'''
Calculate the hashtag from user tweets and save them with userid
'''
def save_hashtag(new_tweets,userName):
    listy = []
    hashy = []
    for i in new_tweets:
        listy = [j['text'] for j in i.entities.get('hashtags')]
        if not listy:
            continue
        else:
            for k in listy:
                hashy.append(k.lower())
    hashtags_list = list(set(hashy))
    if db.hashtags.find_one({'user':userName}) == None: # prevent duplicate tweets being stored
        db.hashtags.save({ 'user' : userName,'hashtagList' : hashtags_list})
    else:
        db.hashtags.update_one({'user': userName},{'$set':{'hashtagList' : hashtags_list}})  
    return hashtags_list

'''
All processed words saved into database, if already present in database updates the 
new keywords
'''
def save_uniqueWords(processedWords, userName):
    if db.spacytopics.find_one({'user':userName}) == None: # prevent duplicate tweets being stored
        db.spacytopics.save({ 'user' : userName,'topics' : processedWords})
    else:
        db.spacytopics.update_one({'user': userName},{'$set':{'topics' : processedWords}})

'''
This method fetches the liked tweets from user timeline
'''
def get_likes(api,userName):
    likes_tweets=api.favorites(count=10,tweet_mode="extended")
    liked = [" ".join([like.full_text]) for like in likes_tweets]
    return liked

'''
This method returns the cleaned most common english keywords with the 
help of spacy library, here passed parameter document is prepared with 
spacy nlp function which is used to get most usefull words from user twitter
timeline.
'''
def get_mostCommon(document):
    spacy_list = []
    pos_tags = {w.pos: w.pos_ for w in document}
    cleaned_list = [clean(word.string) for word in document if not isNoisy(word)]
    cool = Counter(cleaned_list) .most_common(common_token)
    spacy_var = [tup[0] for tup in cool]
    for i in spacy_var:
        spacy_list.append(re.sub(r'[^A-Za-z]', '', i))
    return spacy_list

'''
This method returns the entities like cardinal, person, countries etc.
'''
def get_entities(document):
    entity_list=[]
    labels = set([w.label_ for w in document.ents])
    for label in labels: 
        entities = [clean(e.string, lower=False) for e in document.ents if label==e.label_] 
        entity_list.extend(entities)
        print(label,str(entities))
    return entity_list

'''
This method returns all the likes of prime news article keywords
'''
def get_appLikes(userName):
    ext_likes=[]
    interest_result = db.userslikes.find({'user' : userName})
    for obj in interest_result:
        ext_likes.extend(obj['keywords'])
    return ext_likes

'''
This method returns all the article keywords which are saved in prime 
application by user.
'''
def get_appsaved(userName):
    saved=[]
    interest_result = db.usernews.find({'user' : userName})
    for obj in interest_result:
        saved.extend(obj['keywords']) 
    return saved     
'''
User profile is saved into file and used for user similarty calculation
'''
def save_profile(profile_wordList, userName):   
    completeName = os.path.join(save_path, userName)         
    file1 = open(completeName, "w",encoding='utf8')
    for i in profile_wordList:
        file1.write(i+'\n')
    file1.close()

'''
This method returns the user personalised category list and that is
shown to front end
'''
def get_perCategory(userName):
    # get categories from the collection USER2CATEGORY 
    result = db.user2category.find({'userName' : userName},{'categories':1, '_id':0})
    x = []
    for i in result:
        x.append(i)
    print(x)
    if x == []:
        user2categoryLst = []
    else:
        # user interests list
        user2categoryLst = x[0]["categories"]
    return user2categoryLst

'''
This method saves and updates the user personalisation to database with userName
'''
def update_perCategory(pcid,userName):
    idLst = []
    # split the string and get the user's interest items
    if pcid is not None:
        idLst = pcid.split(',')
    # update collection USER2CATEGORY by user's name
    db.user2category.update_one({'userName' : userName}, {'$set':{'categories': idLst}}, upsert=True)

'''
This method returns the category which user actually intrested and
count according to user category
'''
def  get_normIntrest(tweet_intrest):
    final_intrest_category = []
    normCounts = dict()
    for i in tweet_intrest:
        normCounts[i] = normCounts.get(i, 0) + 1
        final_intrest_category.append(i)

    print(normCounts)
 
    #Putting default value of 0 for categories not present in the classification result
    c_list = ['business','entertainment','politics','sport','technology','gaming','science-and-nature','music']
    for i in c_list:
        if i not in list(normCounts.keys()):
            normCounts[i] = 0
    return final_intrest_category,normCounts

'''
This method assign the score to each recommended article, which
is used to sort the recommended article while presenting them
'''
def assign_score(recom_list,normCounts):
    list_technology=[]
    list_business=[]
    list_politics=[]
    list_sport=[]
    list_entertainment=[]
    list_gaming=[]
    list_general=[]
    list_music=[]
    list_science_and_nature=[]   
    for i in recom_list:
        if i['category'] == "technology":
            i['category_score'] = normCounts['technology']
            list_technology.append(i)
        if i['category'] == "business":
            i['category_score'] = normCounts['business']
            list_business.append(i)
        if i['category'] == "politics":
            i['category_score'] = normCounts['politics']
            list_politics.append(i)
        if i['category'] == "sport":
            i['category_score'] = normCounts['sport']
            list_sport.append(i)
        if i['category'] == "entertainment":
            i['category_score'] = normCounts['entertainment']
            list_entertainment.append(i)
        if i['category'] == "gaming":
            list_gaming.append(i)
            i['category_score'] = normCounts['gaming']
        if i['category'] == "general":
            list_general.append(i)
        if i['category'] == "music":
            list_music.append(i)
            i['category_score'] = normCounts['music']
        if i['category'] == "science-and-nature":
            list_science_and_nature.append(i)
            i['category_score'] = normCounts['science-and-nature']
    
    recom_scoredList = list_technology[:20] + list_business[:20] +list_politics[:20]+ list_sport[:20]+ list_entertainment[:20]+list_gaming[:20]+list_general[:20]+list_music[:20]+list_science_and_nature[:20]
    return recom_scoredList

'''
Hybrid set of articles is recommended to the user which are sorted
according to user category score and according to date and time
'''
def recom_hybridarticles(rcomlist, userName):
    if rcomlist :
        if userName in db.collection_names():
            db[userName].drop()
            db[userName].insert_many(rcomlist)
        else:
            db[userName].insert_many(rcomlist)
    
    hybrid =  db[userName].find().sort([["category_score",pymongo.DESCENDING],["publishedAt",pymongo.DESCENDING]] )
    return hybrid