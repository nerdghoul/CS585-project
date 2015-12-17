from __future__ import division
from gensim import corpora, models, similarities
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import SGDClassifier
import csv
import numpy as np
import random
import time
import math
from matplotlib import pyplot as plt
from collections import defaultdict
from collections import Counter
from sklearn import svm

para_label = ["(3, 2)","(4, 1)","(5, 0)"]
nonpara_label = ["(1, 4)", "(0, 5)"]



"""
Takes either training or test data
Gets relevant information from data, calls fill_featlist for each pair
Also adds corresponding label of each pair of tweet to target list, 
used for y value of classifier.
"""
def construct_dataset(train=True):
	features = []
	target = []

	if train == True:
		path = "train.data"
	else:
		path = "test.data"

	data = []

	with open(path, 'rb') as csv_file:
	    csv_reader = csv.reader(csv_file, delimiter='\t')
	    for row in csv_reader:
	    	d = {}
	    	sent1 = row[2]
	    	sent2 = row[3]
	    	label = row[4]
	    	sent1_tag = row[5]
	    	sent2_tag = row[6]

	    	if train == True:
		    	if label in para_label:
		    		target.append(1)
		    		fill_featlist(features, sent1, sent2, sent1_tag, sent2_tag, label)

		    	if label in nonpara_label:
		    		target.append(0)
		    		fill_featlist(features, sent1, sent2, sent1_tag, sent2_tag, label)

	    	if train == False:
	    		if int(label) > 3:
	    			target.append(1)
	    			fill_featlist(features, sent1, sent2, sent1_tag, sent2_tag, label)

	    		if int(label) < 3:
	    			target.append(0)
	    			fill_featlist(features, sent1, sent2, sent1_tag, sent2_tag, label)

	target = np.array(target)
	return features, target

"""
Creates a feature vector for pairs of tweets (in a dictionary)
Adds feature vector to a global list of features.
"""
def fill_featlist(features, sent1, sent2, sent1_tag, sent2_tag, label):
	feat = {}

	'''
	if label in para_label:
		feat["label"] = 1
	if label in nonpara_label:
		feat["label"] = 0
	'''

	sent1_list = tokenize(sent1)
	sent2_list = tokenize(sent2)
	sent1_pos = getPOS(tokenize(sent1_tag))
	sent2_pos = getPOS(tokenize(sent2_tag))

	feat["sent_cos"] = get_cosine(sent1_list, sent2_list)
	feat["pos_cos"] = get_cosine(sent1_pos, sent2_pos)
	features.append(feat)

"""
Gets the POS tag for each word in a tokenized sentence.
"""
def getPOS(sent_tag):
	pos = []
	for t in sent_tag:
		tag_info = t.split("/")
		pos.append(tag_info[2])
	return pos


"""
Calculates the cosine similarity of words of two sentences. 
Also used to compare the sentences' POS tags.
"""
def get_cosine(sent1, sent2):
	vec1 = Counter(sent1)
	vec2 = Counter(sent2)

	intersection = set(vec1.keys()) & set(vec2.keys())
	numerator = sum([vec1[x] * vec2[x] for x in intersection])

	sum1 = sum([vec1[x]**2 for x in vec1.keys()])
	sum2 = sum([vec2[x]**2 for x in vec2.keys()])
	denominator = math.sqrt(sum1) * math.sqrt(sum2)

	if not denominator:
		return 0.0
	else:
		return float(numerator) / denominator

def tokenize(doc):
    tokens = doc.split()
    lowered_tokens = [t.lower() for t in tokens]
    return lowered_tokens



feats, target = construct_dataset()
vec = DictVectorizer()
X = vec.fit_transform(feats)

"""
The following is mostly a test to make sure dataset is formatted correctly.

Gaussian Naive Bayes prediction of a paraphrase using only sentential cosine distance 
and cosine distance of part of speech tags, only on test data.

"""

print vec.get_feature_names()
print X.shape
print target.shape
gnb = GaussianNB()
y_pred = gnb.fit(X.toarray(), target).predict(X.toarray())

print("Number of mislabeled points out of a total %d points : %d"
	% (X.shape[0],(target != y_pred).sum()))



"""
Evaluation of performance on test set using MultinomialNB
"""
test_feats, test_target = construct_dataset(train=False)
print test_target

clf = MultinomialNB().fit(X, target)
test_vec = DictVectorizer()
test_X = test_vec.fit_transform(test_feats)

predicted = clf.predict(test_X)
print np.mean(predicted == test_target)

"""
Evaluation of performance on test set using linear SVM
"""
feats, target = construct_dataset()
vec = DictVectorizer()
X = vec.fit_transform(feats)

test_feats, test_target = construct_dataset(train=False)
test_vec = DictVectorizer()
test_X = test_vec.fit_transform(test_feats)

svm = SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, n_iter=5, random_state=42).fit(X, target)
predicted = svm.predict(test_X)
print np.mean(predicted == test_target)



"""
def make_feat_vec(sent1, sent2, sent1_tag, sent2_tag, label):
	feat_vec = defaultdict(float)
	for n in range(len(sent1) - 1):
		for i in range(len(sent2) - 1):
			feat_vec["str_%s_%s_%s" % (label, sent1[n], sent2[i])] = string_features(sent1[n], sent2[i])
			feat_vec["pos_%s_%s_%s" % (label, sent1[n], sent2[i])] = pos_features(getPOS(sent1_tag[n]), getPOS(sent2_tag[i]))

	return feat_vec



def create_sims(data_dict):
	documents = []
	documents.append(data_dict["sent1"])
	stoplist = set('for a of the and to in'.split())
	texts = [[word for word in document.lower().split() if word not in stoplist] for document in documents]
	frequency = defaultdict(int)
	for text in texts:
		for token in text:
			frequency[token] += 1

	texts = [[token for token in tex if frequency[token] > 1] for text in texts]
	dictionary = corpora.Dictionary(texts)
	new_vec = dictionary.doc2bow(data_dict["sent2"].lower().split())
	print new_vec
	corpus = [dictionary.doc2bow(text) for text in texts]
	tfidf = models.TfidfModel(corpus)
	print tfidf[new_vec]

data = construct_dataset()
create_sims(data[0])
dict_vectorizer = DictVectorizer()
vectorized = dict_vectorizer.fit_transform(data)


def create_vocab(train=True):
	if train == True:
		path = "train.data"
	else:
		path = "test.data"
	vocab = []
	with open(path, 'rb') as csv_file:
	    csv_reader = csv.reader(csv_file, delimiter='\t')
	    for row in csv_reader:
	    	vocab.append(row[2])
	    	vocab.append(row[3])
	return vocab

vectorizer = CountVectorizer()
vocab = create_vocab()
X = vectorizer.fit_transform(vocab)
counts = X.toarray()

transformer = TfidfTransformer()

tfidf = transformer.fit_transform(counts)
print tfidf

def get_tfidf(sent1, sent2):
	vocab = [sent1, sent2]
	vectorizer = CountVectorizer(binary=True)
	X = vectorizer.fit_transform(vocab)
	counts = X.toarray()
	transformer = TfidfTransformer()
	tfidf = transformer.fit_transform(counts)
	return tfidf.toarray()


"""