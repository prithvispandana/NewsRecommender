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


#each profile is stored in one document either in local or database
all_profiles=[] #List is created to store all profiles
profiles_id=[]
for filename in glob.glob('data/*'): #include all the files from current directory
    fin = open(filename,"r")  #open the file for reading
    profiles_id.append(os.path.basename(filename)) #document name for future reference
    all_profiles.append(fin.read()) #read full content of file and added to the client
    fin.close() #close the file
print("Number of profiles %d" % len(all_profiles)) #Total number of profiles


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
tf_idfVector = TfidfVectorizer(stop_words="english",min_df =1,ngram_range=(1,1))#chosen n-gram of three words. It will produce phrases containing upto three words
tf_idfMatrix= tf_idfVector.fit_transform(all_profiles)
cosSim=cosine_similarity(tf_idfMatrix)
df = pd.DataFrame(cosSim,columns=profiles_id,index=profiles_id)
print(df)
print(df['110273156'].argmax())
#print(df.to_dict())
#print( df.groupby('110273156').head(2))

