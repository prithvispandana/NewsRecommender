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

sched = BlockingScheduler()

#each profile is stored in one document either in local or database
#document name must be profile_id
all_profiles=set() #List is created to store all profiles
profiles_id=set()
access_df={}
def load_profiles():
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
    global access_df
    access_df=df.to_dict()
    df=pd.DataFrame()


def getTopN(user, topN):
     load_profiles()
     calc_sim()
     topUsers=sorted(access_df[user], key=access_df[user].get, reverse=True)[:topN+1]
     topNusers=[]
     if not topUsers:
         for i in range(1,topN+1):
             topNusers.append(topUsers[i])
     return topNusers
 

# @sched.scheduled_job('interval', seconds=30)
# def job_scheduler():
#     load_profiles()
#  
#  
# @sched.scheduled_job('interval', seconds=50)
# def job_scheduler():
#     if all_profiles is not None:
#         calc_sim()
# #print(df.to_dict())
# #print( df.groupby('110273156').head(2))
#  
# sched.start()
