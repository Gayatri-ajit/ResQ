from sqlalchemy import create_engine
import numpy as np
import pandas as pd
import re
import nltk
import seaborn as sns
import time
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem import WordNetLemmatizer
import matplotlib.pyplot as plt
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
#TfidfVectorizer = CountVectorizer + TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from sklearn.multioutput import MultiOutputClassifier
#from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split,GridSearchCV
from sklearn.metrics import classification_report
import pickle
import sys
import os
import sys
sys.path.append('C:/Users/soory/OneDrive/Desktop/mini_pro/ResQ1/')

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath('C:/Users/soory/OneDrive/Desktop/mini_pro/ResQ1/models'))
  
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)
  
# adding the parent directory to 
# the sys.path.
sys.path.append(parent)

from utils import Text_clean

nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')



def load_data(database_filepath):
    '''
    INPUT:
        database_filepath:relative filepath of database
    OUTPUT:
        X: the original messages
        Y: the classified results of disaster response
        category_name:the list of names for Y columns
    DESCRIPTION:
        The function is to load data from database, and assign corrected collumns to X,Y
    
    '''
    engine = create_engine('sqlite:///C:/Users/soory/OneDrive/Desktop/mini_pro/ResQ1/data/DisasterResponse.db')
    df=pd.read_sql_table('message',con=engine)
    X=df['message']
    Y = df.iloc[ : , -36:]
    Y = Y.drop(['related','child_alone'],axis=1)
    category_name = Y.columns
    return X,Y,category_name
'''
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
'''

def build_model():
    '''
    Build a machine learning model using the pipeline
    OUTPUT:
        CV: the model with the optimized parameters
    '''
    pipeline = Pipeline([
        ('tfidvectorizer', TfidfVectorizer(tokenizer=Text_clean.tokenize)),#override the tokenizer with customized one
        ('clf', MultiOutputClassifier(SGDClassifier(n_jobs = -1,random_state=6)))]
        )

    parameters = {
        'clf__estimator__alpha': [0.0001,0.001],
        'clf__estimator__penalty':['l2'],
        'clf__estimator__loss':['hinge']
    }

    cv = GridSearchCV(pipeline,parameters,cv=3)
    return cv

def evaluate_model(model, X_test, Y_test, category_name):
    '''
    print out classification report and accuracy scode for the best model result
    '''
    Y_test_pred = model.predict(X_test)
    Y_test_pred = pd.DataFrame(data=Y_test_pred, 
                          index=Y_test.index, 
                          columns=category_name)
    #print('Accuracy score:\n'.format(accuracy_score(Y_test, Y_test_pred)))
    print(classification_report(Y_test, Y_test_pred, target_names=category_name))

def save_model(model, model_filepath):
    '''
    Export the model as a pickle file
    '''
    with open(model_filepath,'wb') as f:
        pickle.dump(model,f)
        f.close()

def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_name = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2,random_state=6)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_name)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')

def p_tokenize(text):
    '''
    INPUT:
        text:raw message
    OUTPUT:
        X:tokenized words
    DESCRIPTION:
        The dunction is to process the scentence, normalize texts, tokenize texts.
        Convert all cases to lower cases, remove extra space,stop words, and 
        reduce words to their root form.
    '''
    clean_tokens=[]    
    #remove punctuation,normalize case to lower cases, and remove extra space
    text = re.sub(r"[^a-zA-Z0-9]"," ",text.lower()).strip()
    
    #tokenize text
    tokens=word_tokenize(text)
    
    
    for w in tokens:  
        #remove stop words
        if w not in stopwords.words("english"):
        #lemmatization
        #reduce words to their root form
            lemmed = WordNetLemmatizer().lemmatize(w)
            clean_tokens.append(lemmed)
    return clean_tokens

if __name__ == '__main__':
    main()