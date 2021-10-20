'''
This programme is to analyze topics of discussion
within each emotion category using topic modeling.
Each .csv file has been provided based on the sentiment
analysis of discussions on Twitter and Reddit.

Columns are:
Row Number, Text, Score, Date, Link
'''

# Chapter 1: Initialize data to be 'cleaned'
import re
from os import remove
import pandas as pd
df = pd.read_csv('neutral.csv')
df.head()

# Chapter 2: Clean Data
'''
Removing Non-English words is crucial in this task of topic modeling
as the task requires analysis of each topic within each emotion category
For the simplicity of the task, non-English words are removed. SpaCy,
nltk and re is used for this chapter.
'''
# Initiate cleaning stage.
# import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
import string
import nltk
import spacy
from spacy.language import Language
from spacy_langdetect import LanguageDetector

# Stopwords to remove 'useless' words
sWords = stopwords.words('english')
nltk.download('words', quiet=True)
sWords.extend(['got', 'say', 'use', 'from', 'nt', 'gt', 'to', 'also', 'that', 'this', 'the'])
setStopWords = set(sWords)
puncExclude = set(string.punctuation)
engWords = set(nltk.corpus.words.words())
lemma = WordNetLemmatizer()

# Load Spacy Languge Support
nlp = spacy.load('en_core_web_sm')

# Assign English Language detector to appropriate function
def get_lang_detector(nlp, name):
    return LanguageDetector()
Language.factory("language_detector", func=get_lang_detector)
nlp.add_pipe("language_detector", last=True)

# Initialise Data Cleaning
# Remove URLs
df['cleanText'] = df['text'].apply(lambda x: re.split('https:\/\/.*', str(x))[0])

# Input all text values into a list.
# Each text value will be referred to in this code as a document.
data = df.cleanText.values.tolist()

def clean(doc):
    wordTokens = word_tokenize(doc)

    # Remove Non-English words
    removeNonEng = " ".join(w for w in wordTokens if w.lower() in engWords or not w.isalpha())

    # Remove Usernames
    removeusernames = " ".join(filter(lambda x:x[0]!='@', removeNonEng.split()))
    
    # Remove Punctuations
    removepunc = removeusernames.translate(str.maketrans('', '', string.punctuation))
    extrapunc = ["“", "’",'"',"'", "`", "≈"]
    for i in extrapunc:
        removepunc = removepunc.replace(i, '')
    
    print(removepunc.split())
    # Remove numbers
    removenum = [x for x in removepunc.split().split() if not isinstance(x, int)]

    # Normalize Corpus
    normaldata = " ".join(lemma.lemmatize(word) for word in removenum)

    # Remove Stopwords
    removesw = " ".join([x for x in normaldata.split() if not x.lower() in setStopWords])
    
    # Final Removal of Non-English Sentences
    data1 = nlp(removesw)
    finalData = ""
    for sent in data1.sents:
        if (sent._.language)['language'] == 'en':
            finalData += str(sent)
    return finalData

# Data cleaning completed.
cleanData = [clean(doc).split() for doc in data]

# Chapter 3: Prepare Document-Term Matrix
'''
All of the rows in the 'text' column, when combined
together, is known as the corpus. Converting this 
into matrix representation allows LDA model to
easily find repeating term patterns in the DT matrix.
For this, we'll use gensim.
'''

import gensim
from gensim import corpora

# Create term dictionary for corpus
corpdict = corpora.Dictionary(cleanData)

# Convert list of documents into DTM using above dictionary
docTermMatrix = [corpdict.doc2bow(doc) for doc in cleanData]

# Creating LDA model using gensim
Lda = gensim.models.ldamodel.LdaModel

# Run and Train LDA model on the DTM
model = Lda(docTermMatrix, num_topics=10, id2word=corpdict, passes=50)

# Result here
#print(model.print_topics(num_topics=50, num_words=20))

# Chapter 4: Visualizing each Topic into a Wordcloud
from matplotlib import pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import matplotlib.colors as mcolors

# Coloring scheme for each topic
cols = [color for name, color in mcolors.TABLEAU_COLORS.items()]  # more colors: 'mcolors.XKCD_COLORS'

cloud = WordCloud(stopwords=setStopWords,
                  background_color='white',
                  width=2500,
                  height=1800,
                  max_words=25,
                  colormap='tab10',
                  color_func=lambda *args, **kwargs: cols[i],
                  prefer_horizontal=1.0)

topics = model.show_topics(formatted=False)

fig, axes = plt.subplots(2, 2, figsize=(10,10), sharex=True, sharey=True)

for i, ax in enumerate(axes.flatten()):
    fig.add_subplot(ax)
    topicWords = dict(topics[i][1])
    cloud.generate_from_frequencies(topicWords, max_font_size=300)
    plt.gca().imshow(cloud, interpolation='bilinear')
    plt.gca().set_title('Topic ' + str(i), fontdict=dict(size=16))
    plt.gca().axis('off')

plt.subplots_adjust(wspace=0, hspace=0)
plt.axis('off')
plt.margins(x=0, y=0)
plt.tight_layout()
plt.show()

# Chapter 5: Visualizing Topics via word counts of keywords
'''from collections import Counter
topics = model.show_topics(formatted=False)
data_flat = [w for w_list in cleanData for w in w_list]
counter = Counter(data_flat)

out = []
for i, topic in topics:
    for word, weight in topic:
        out.append([word, i , weight, counter[word]])

df = pd.DataFrame(out, columns=['word', 'topic_id', 'importance', 'word_count'])        

# Plot Word Count and Weights of Topic Keywords
fig, axes = plt.subplots(2, 2, figsize=(16,10), sharey=True, dpi=160)
cols = [color for name, color in mcolors.TABLEAU_COLORS.items()]
for i, ax in enumerate(axes.flatten()):
    ax.bar(x='word', height="word_count", data=df.loc[df.topic_id==i, :], color=cols[i], width=0.5, alpha=0.3, label='Word Count')
    ax_twin = ax.twinx()
    ax_twin.bar(x='word', height="importance", data=df.loc[df.topic_id==i, :], color=cols[i], width=0.2, label='Weights')
    ax.set_ylabel('Word Count', color=cols[i])
    ax_twin.set_ylim(0, 0.030); ax.set_ylim(0, 3500)
    ax.set_title('Topic: ' + str(i), color=cols[i], fontsize=16)
    ax.tick_params(axis='y', left=False)
    ax.set_xticklabels(df.loc[df.topic_id==i, 'word'], rotation=30, horizontalalignment= 'right')
    ax.legend(loc='upper left'); ax_twin.legend(loc='upper right')

fig.tight_layout(w_pad=2)    
fig.suptitle('Word Count and Importance of Topic Keywords', fontsize=22, y=1.05)    
plt.show()'''
