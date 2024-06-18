from flask import Flask, request,jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
#from pymongo import MongoClient
import urllib
import sqlite3
import requests
import json
import plotly
import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

import joblib
#from sklearn.base import BaseEstimator, TransformerMixin
from sqlalchemy import create_engine
#import dill as pickle
import utils

app = Flask(__name__)

DATABASE_FILE = 'registered_users.db'
engine = create_engine('sqlite:///'+'data/DisasterResponse.db')
df = pd.read_sql_table('message', engine)
df_redefine = df.iloc[ : , -36:]
df_redefine = df_redefine.drop(['related','child_alone'],axis=1)
df_redefine_columnnames = list([x.replace('_', ' ') for x in df_redefine])
# Twilio credentials
account_sid = 'ACeea5050fbd4790e9bd634d53bb2eeb46'
auth_token = 'fb598c1fbe4d55523ef5aa5ca1db2ef2'
client = Client(account_sid, auth_token)

def create_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            phone_number TEXT PRIMARY KEY,
            name TEXT,emergency TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_database()
def insert_user(phone_number, name, emergency):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (phone_number, name, emergency) VALUES (?, ?, ?)', (phone_number, name, emergency))
    conn.commit()
    conn.close()

def update_user(phone_number, name, emergency):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET name = ? WHERE phone_number = ?', (name, phone_number, emergency))
    conn.commit()
    conn.close()

def get_user(phone_number):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE phone_number = ?', (phone_number,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_emergency_contact(phone_number):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT emergency FROM users WHERE phone_number = ?', (phone_number,))
    emergency_contact = cursor.fetchone()
    conn.close()
    return emergency_contact

def calling(emergency):

    message=client.messages.create(
        body="Gayatri is stuck in a flood. Please stay calm. We're ensuring her safety and will keep you updated.",
        from_='+19033475682',
        to=emergency
    )


    print(message.body)

    call = client.calls.create(
        url='http://demo.twilio.com/docs/voice.xml',  # URL for TwiML instructions
        to=emergency,
        from_='+19033475682'
    )

    print(call.sid)


step=0

#mclient=MongoClient("mongodb+srv://jonasstark861:kYbxjto1dhZNsTgf@cluster0.uwxlttk.mongodb.net/")


# URL of your Flask app for message classification
CLASSIFICATION_URL = "http://localhost:5002/go"
model = joblib.load('models/classifier.pkl')

@app.route('/whatsapp_bot', methods=['POST'])
def whatsapp_bot():
    # Parse incoming message from Twilio
    incoming_message = request.values.get('Body', '').lower()
    global step
    # Get user's phone number
    phone_number = request.values.get('From')
    existing_user = get_user(phone_number)
    # Check if the user is registered
    if step==0: 
        if existing_user is not None:
            # User is registered, handle other commands
            if "hello" in incoming_message:
                response_message = "Hello! Welcome back to the WhatsApp bot."
            elif "custom1" in incoming_message:
                response_message = "This is a custom message for scenario 1."
            elif "custom2" in incoming_message:
                response_message = "Here's another custom message for scenario 2."
            elif 'Latitude' in request.values and 'Longitude' in request.values:
                # Extract location data
                latitude = request.values.get('Latitude')
                longitude = request.values.get('Longitude')
                print("location")
                emergency_contact = get_emergency_contact(phone_number)
                response_message = f"Received location: Latitude - {latitude}, Longitude - {longitude}.\nCalling emergency number... "
                calling(emergency_contact)
                

            elif 'MessageType' in request.values and request.values.get('MessageType') == 'contacts':
                # Extract vCard URL from the request
                vcard_url = request.values.get('MediaUrl0')

                # Download the vCard file
                with urllib.request.urlopen(vcard_url) as response:
                    vcard_data = response.read().decode('utf-8')

                # Process the vCard data (e.g., parse and extract contact information)
                # Here, you can implement your logic to parse the vCard data

                # Example response
                response_message = "Received a contact vCard attachment."
            else:
                # classification_response = requests.get(CLASSIFICATION_URL, params={'query': incoming_message})
                # print("Response content:", classification_response.text)  # Print out response content
                # classification_result = classification_response.json()
                
                # # Process classification result
                # # For example, you can construct a response based on the classification
                # response_message = "Your message is classified as:\n"
                # for category, label in classification_result.items():
                #     response_message += f"{category}: {label}\n"
                query=incoming_message
                classification_labels = model.predict([query])[0]
                print('Classification labels',classification_labels)
                classification_results = dict(zip(df_redefine_columnnames, classification_labels))
                print('Classification results',classification_results)
                # Extract disasters with value 1 from classification_results
                active_disasters = [disaster.replace('_', ' ') for disaster, value in classification_results.items() if value == 1]

                # Construct response message
                response_message = "Is this the emergency you are facing? Please respond with Y or N\n"
                step=1
                if active_disasters:
                    response_message += '\n'.join(active_disasters)
                else:
                    response_message += "No disasters detected."

                # Print or return the response message
                print(response_message)


        else:
            # Check if the message is a location message
            if incoming_message.startswith('num'):
                # Process registration
                # Extract name from the message
                emergency = incoming_message.split(' ', 1)[1]
                # Store user registration details
                insert_user(phone_number,"", emergency)
                response_message = f"Hello, your emergency contact has been entered. How can I assist you?"
            else:
                response_message = "Hello new user, please type \"num YourEmergencyContact\" "
    elif step==1:
        if 'y' in incoming_message:
            response_message="Please type E to contact emergency services or Type S for me to give you emergency response steps"
            step=2
            print(response_message)

        elif 'n' in incoming_message:
            response_message="Sorry for the misreading the situation can you tell again about your emergency"
            step=0
            print(response_message)
    elif step==2:
        if 'e' in incoming_message:
            response_message="Please send me your location to contact emergency service"
            step=0
            print(response_message)
        elif 's' in incoming_message:
            response_message="These are the things you can do"
            print(response_message)
  
        

            
        
        # Send response back to the user
    twilio_response = MessagingResponse()
    twilio_response.message(response_message)

    return str(twilio_response)

if __name__ == '__main__':
    app.run(debug=True)








# @app.route('/whatsapp_bot', methods=['POST'])
# def whatsapp_bot():
#     # Parse incoming message from Twilio
#     incoming_message = request.values.get('Body', '').lower()

#     # Get user's phone number
#     phone_number = request.values.get('From')
#     existing_user = get_user(phone_number)
#     # Check if the user is registered
#     if existing_user is not None:
#         # User is registered, handle other commands
#         if "hello" in incoming_message:
#             response_message = "Hello! Welcome back to the WhatsApp bot."
            
#         elif "help" in incoming_message:
#             response_message = "Sure, I'm here to help. What do you need assistance with?"
#         elif "custom1" in incoming_message:
#             response_message = "This is a custom message for scenario 1."
#         elif "custom2" in incoming_message:
#             response_message = "Here's another custom message for scenario 2."
#         elif 'Latitude' in request.values and 'Longitude' in request.values:
#             # Extract location data
#             latitude = request.values.get('Latitude')
#             longitude = request.values.get('Longitude')

#             # Process and store location data (replace this with your logic)
#             response_message = f"Received location: Latitude - {latitude}, Longitude - {longitude}"

#         elif 'MessageType' in request.values and request.values.get('MessageType') == 'contacts':
#         # Extract vCard URL from the request
#             vcard_url = request.values.get('MediaUrl0')

#         # Download the vCard file
#             with urllib.request.urlopen(vcard_url) as response:
#                 vcard_data = response.read().decode('utf-8')

#         # Process the vCard data (e.g., parse and extract contact information)
#         # Here, you can implement your logic to parse the vCard data

#         # Example response
#             response_message = "Received a contact vCard attachment."
#         else:
#             response_message = "Sorry, I didn't understand that. Can you please rephrase?"
#     else:
#         # Check if the message is a location message
#         if incoming_message.startswith('num'):
#             # Process registration
#             # Extract name from the message
#             emergency = incoming_message.split(' ', 1)[1]
#             # Store user registration details
#             insert_user(phone_number, emergency, "")
#             response_message = f"Hello ,your emergency contact has been entered .How can i assist u"
#         else:
#            response_message="Hello new user please type \"num YourEmergencyContact\" "
#     # Send response back to the user
#     twilio_response = MessagingResponse()
#     twilio_response.message(response_message)

#     return str(twilio_response)

# if __name__ == '__main__':
#     app.run(debug=True)





 