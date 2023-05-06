import os
import requests
import json
import pandas as pd
from flask import Flask, Response,request

# constants
TOKEN = '6225260399:AAEc43t9xjwJpj0LgBYdNkmhkoBsygUh0-o'

# info bot
# https://api.telegram.org/bot6225260399:AAEc43t9xjwJpj0LgBYdNkmhkoBsygUh0-o/getMe

# get updates
# https://api.telegram.org/bot6225260399:AAEc43t9xjwJpj0LgBYdNkmhkoBsygUh0-o/getUpdates

# Webhook
# https://api.telegram.org/bot6225260399:AAEc43t9xjwJpj0LgBYdNkmhkoBsygUh0-o/setWebhook?url=https://telegram-rossmann-bot-xcy0.onrender.com

# send Messages
# https://api.telegram.org/bot6225260399:AAEc43t9xjwJpj0LgBYdNkmhkoBsygUh0-o/sendMessage?chat_id=877076406&text=Hi, I am doing great, tks!


def send_message(chat_id, text):
    url = 'https://api.telegram.org/bot{}/'.format(TOKEN)
    url = url + 'sendMessage?chat_id={}'.format(chat_id)
    r = requests.post (url, json={'text': text})
    print('Status Code{}'.format(r.status_code))

    return None 

def load_dataset(store_id):
    # Test dataset
    df_test_raw = pd.read_csv('data/test.csv')
    df_store_raw = pd.read_csv('data/store.csv')

    # Merging test + store dataset
    df_test = pd.merge(df_test_raw, df_store_raw, how='left', on='Store')

    # Choosing only one store for prediction test
    df_test = df_test[df_test['Store'] == store_id]

    if not df_test.empty:
        # Removing closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis=1)

        # Converting dataframe to json
        data = json.dumps(df_test.to_dict(orient='records'))

    else:
        data = 'error'

    return data

def predict(data):

    # API Call
    url = 'https://webapp-rossmann-8290.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    return d1

def parse_message(message):

    try:
        chat_id = message['message']['chat']['id']
    except:
        chat_id = message['edited_message']['chat']['id']
            
    try:
        store_id = message['message']['text']
        
    except:
        store_id= message['edited_message']['text']

    store_id = store_id.replace('/', '')

    try:
        store_id = int(store_id)

    except ValueError:

        if store_id.lower() == 'start':
            msg = 'Welcome to Rossmann Sales Forecast Bot! Please type "/" + the store number you want to know the sales forecast'
            send_message(chat_id, msg)

        elif store_id.lower() == 'hi' or store_id.lower() == 'hello':
            send_message(chat_id, msg)

        elif store_id.lower() == 'bye':
            send_message(chat_id, 'Bye!')

        else:
            send_message(chat_id, 'Store ID not typed correctly')
        
        store_id = 'error'

    return chat_id, store_id

# API initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message (message)

        if store_id != 'error':
            #loading data
            data = load_dataset(store_id)

            if data != 'error':
                #prediction
                d1 = predict(data)

                #calculation
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()

                #send message
                msg = 'Store number {} will sell ${:,.2f} in the next 6 weeks'.format(d2['store'].values[0], d2['prediction'].values[0])
                
                send_message(chat_id, msg)
                return Response('Ok', status=200)
                

            else:
                send_message(chat_id, 'Sorry, this store is currently not available')
                return Response('Ok', status=200)
        
        else:
            send_message(chat_id, 'Store ID is wrong')
            return Response('Ok', status=200)

    else:
        return '<h1> Rossmann Telegram Bot by Marcelo Rissi </h1>'
    

if __name__== '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=5000)
