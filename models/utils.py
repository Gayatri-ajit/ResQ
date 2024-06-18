
from sklearn.base import BaseEstimator, TransformerMixin
import re
import nltk
import time
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem import WordNetLemmatizer
import joblib
from sklearn.base import BaseEstimator, TransformerMixin



nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')

class Text_clean(BaseEstimator, TransformerMixin):
    def tokenize(text):
        tokens = word_tokenize(text)
        lemmatizer = WordNetLemmatizer()
        clean_tokens = []
        text = re.sub(r"[^a-zA-Z0-9]"," ",text.lower()).strip()
        for w in tokens:  
        #remove stop words
            if w not in stopwords.words("english"):
            #lemmatization
            #reduce words to their root form
                lemmed = WordNetLemmatizer().lemmatize(w)
                clean_tokens.append(lemmed)
        return clean_tokens
