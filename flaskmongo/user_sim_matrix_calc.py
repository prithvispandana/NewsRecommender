'''
Created on 13 Jun 2017

@author: nitendra
'''


import glob #find the all path names with matching a specified pattern
import os
import nltk
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from apscheduler.schedulers.blocking import BlockingScheduler
import json
from pymongo import MongoClient
client = MongoClient()
client = MongoClient('mongodb://localhost:27017')
sched = BlockingScheduler()


db = client.tweets_db

#each profile is stored in one document either in local or database
#document name must be profile_id
all_profiles=set() #List is created to store all profiles
profiles_id=set()
def load_profiles():
    global all_profiles #List is created to store all profiles
    global profiles_id
    all_profiles.clear()
    profiles_id.clear()
    for filename in glob.glob('files/*'): #include all the files from current directory
        fin = open(filename,"r",encoding='utf8')  #open the file for reading
        profiles_id.add(os.path.basename(filename)) #document name for future reference
        all_profiles.add(fin.read()) #read full content of file and added to the client
        fin.close() #close the file
#print("Number of profiles %d" % len(all_profiles)) #Total number of profiles


from sklearn.feature_extraction.text import CountVectorizer
# define the function for lemmatization
def lemma_tokenizer(text):
    # use the standard scikit-learn tokenizer first
    standard_tokenizer = CountVectorizer().build_tokenizer()
    tokens = standard_tokenizer(text)
    # then use NLTK to perform lemmatisation on each token
    lemmatizer = nltk.stem.WordNetLemmatizer()
    lemma_tokens=[]
    for token in tokens:
        if re.search('[a-zA-Z]', token):  # save those which are non-numeric
            lemma_tokens.append(lemmatizer.lemmatize(token))
    return lemma_tokens

# we can pass in the same preprocessing parameters
def calc_sim():
    tf_idfVector = TfidfVectorizer(stop_words="english",min_df =1,ngram_range=(1,1))#chosen n-gram of three words. It will produce phrases containing upto three words
    tf_idfMatrix= tf_idfVector.fit_transform(all_profiles)
    cosSim=cosine_similarity(tf_idfMatrix)
    df = pd.DataFrame(cosSim,columns=profiles_id,index=profiles_id)
    print(df)
#     global access_df
#     access_df=df.to_dict()
#     df1 = pd.DataFrame.from_dict(access_df)
    if "sim_col" in db.collection_names():
        db.sim_col.drop()
    if "list_user" in db.collection_names():
        db.list_user.drop()  
    db.list_user.save({"index" : list(profiles_id)})  
    records = json.loads(df.T.to_json()).values()
    db.sim_col.insert(records)
    df=pd.DataFrame()


# def getTopN(user, topN):
#     load_profiles()
#     calc_sim()
#     df2 = read_mongo(db, 'sim_col')
#     print(df2)
#     return list(df2.columns.values)
#  
# 
# def read_mongo(db, collection, query={}, no_id=True):
#     """ Read from Mongo and Store into DataFrame """
#  
#     # Make a query to the specific DB and Collection
#     cursor = db[collection].find(query)
#     # Expand the cursor and construct the DataFrame
#     df =  pd.DataFrame(list(cursor))
#     # Delete the _id
#     if no_id:
#         del df['_id']
#     return df


@sched.scheduled_job('interval', seconds=40)
def job_scheduler():
    all_profiles=set() #List is created to store all profiles
    profiles_id=set()
    load_profiles()
  
  
@sched.scheduled_job('interval', seconds=50)
def job_scheduler():
    if all_profiles:
        calc_sim()
#print(df.to_dict())
#print( df.groupby('110273156').head(2))
  
sched.start()
