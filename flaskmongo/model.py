#http://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_20newsgroups.html
#http://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_files.html#sklearn.datasets.load_files
#http://scikit-learn.org/stable/tutorial/text_analytics/working_with_text_data.html#loading-the-20-newsgroups-dataset
from sklearn.datasets import load_files
from sklearn.feature_extraction.text import CountVectorizer

categories = ['business', 'entertainment','politics', 'sport','tech']

#https://stackoverflow.com/questions/12468179/unicodedecodeerror-utf8-codec-cant-decode-byte-0x9c
twenty_train = load_files(container_path='bbc',categories=categories, shuffle=True, random_state=42,load_content=True,encoding = 'utf-8',decode_error='ignore')

count_vect = CountVectorizer()
X_train_counts = count_vect.fit_transform(twenty_train.data)
    #print(X_train_counts.shape)

from sklearn.feature_extraction.text import TfidfTransformer
# tf_transformer = TfidfTransformer(use_idf=False).fit(X_train_counts)
# X_train_tf = tf_transformer.transform(X_train_counts)
#     #print(X_train_tf.shape)

tfidf_transformer = TfidfTransformer()
X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)

from sklearn.naive_bayes import MultinomialNB
clf = MultinomialNB().fit(X_train_tfidf, twenty_train.target)