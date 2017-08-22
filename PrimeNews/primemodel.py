from sklearn.datasets import load_files
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
import pickle

#defined categories in prime data
categories = ['business', 'entertainment','politics', 'sport','technology','music','science-and-nature','gaming']

#load all the files
prime_train = load_files(container_path='prime',categories=categories, shuffle=True, random_state=42,load_content=True,encoding = 'utf-8',decode_error='ignore')

#Transform the data to feature vector
count_vect = CountVectorizer()
bbc_vectorizer = count_vect.fit_transform(prime_train.data)

#Tf-Idf fit for counted vector to avoid the document which has higher word count
tfidf_transformer = TfidfTransformer()
X_train_tfidf = tfidf_transformer.fit_transform(bbc_vectorizer)

#Multinomial db naive bayes classifier train
multidbfit = MultinomialNB().fit(X_train_tfidf, prime_train.target)
with open('primemodel.pkl', 'wb') as fout:
  pickle.dump((count_vect, multidbfit,prime_train), fout)
