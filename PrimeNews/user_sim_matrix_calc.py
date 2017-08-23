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
all_profiles=set() #set is created to store all profiles
profiles_id=set()  #Each user name is considered as profiles id and stored in set

'''
This method loads all the profiles in all_profiles along with profiles_id

'''
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

'''
This method calculate the similarity with the help of loded profiles and save the
matrix into database, so it is easily accessible in application
'''
def calc_sim():
    tf_idfVector = TfidfVectorizer(stop_words="english",min_df =1,ngram_range=(1,1))#chosen n-gram of three words. It will produce phrases containing upto three words
    tf_idfMatrix= tf_idfVector.fit_transform(all_profiles) #to avoid higher count of similar word in document
    cosSim=cosine_similarity(tf_idfMatrix) #tf-idf vector is passed to cosinesimilarity function to calcualte similarity between documents
    df = pd.DataFrame(cosSim,columns=profiles_id,index=profiles_id) #cosine similarity function is stored 
    print(df)
    if "sim_col" in db.collection_names(): #If similarity collection is present in database drop it
        db.sim_col.drop()
    if "list_user" in db.collection_names(): #user profiles collection is present in database delete it
        db.list_user.drop()  
    db.list_user.save({"index" : list(profiles_id)})  #stores profiles names in database
    records = json.loads(df.T.to_json()).values() #convert dataframe to json for storage
    db.sim_col.insert(records) #Insert similarity records in database
    df=pd.DataFrame()

'''
This is schedular which is loding profiles in memory collections
'''
@sched.scheduled_job('interval', seconds=30)
def job_scheduler():
    all_profiles=set() #set is created to store all profiles
    profiles_id=set() #set is created to store all profiles_id
    load_profiles()
  
'''
This schedular method calculates the similarity from loded profiles
'''  
@sched.scheduled_job('interval', seconds=50)
def job_scheduler1():
    if all_profiles: #if all_profiles loded similarity function is called
        calc_sim() 
sched.start()


#Note: It is possible schedular can miss defined execution but this is not 
#problem it will automatically handled, good part of scheduler is that, if any
#exception occur during the execution of any part because of data loading or index
#may not occur next time, because every execution is new exectution at defined point of time
