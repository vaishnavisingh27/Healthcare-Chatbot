from flask import Flask, render_template, request, jsonify, send_from_directory
import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model

app = Flask(__name__)

# Load necessary data and model
lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_simplilearnmodel.h5')

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})

    if not return_list:
        return None
    
    return return_list

def get_bot_response(intents_list):
    if not intents_list:
        return "Bye! See you later."
    
    tag = intents_list[0]['intent']
    list_of_intents = intents['intents']
    for intent in list_of_intents:
        if intent['tag'] == tag:
            response = random.choice(intent['responses'])
            break
    
    return response

def format_bot_response(response):
    if '\n' in response:
        response_lines = response.split('\n')
        formatted_response = "<br>".join(response_lines)
        return formatted_response
    else:
        return response

def handle_user_input(user_input):
    matched_pattern = False
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            if pattern.lower() in user_input.lower():
                matched_pattern = True
                break
        if matched_pattern:
            break

    if not matched_pattern:
        error_response = "Error - Input does not match."
        formatted_error_response = format_bot_response(error_response)
        return formatted_error_response
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.form['message']
    user_input_error = handle_user_input(user_message)
    if user_input_error:
        return jsonify({'response': user_input_error})
    else:
        intents_list = predict_class(user_message)
        if intents_list:
            response = get_bot_response(intents_list)
            formatted_response = format_bot_response(response)
        else:
            formatted_response = format_bot_response("Error - Input does not match.")
        return jsonify({'response': formatted_response})

# Route to serve static files (images)
@app.route('/images/<path:path>')
def send_images(path):
    return send_from_directory('images', path)

if __name__ == '__main__':
    app.run(debug=True)
