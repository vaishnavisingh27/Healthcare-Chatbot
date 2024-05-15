import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model
import tkinter as tk
from PIL import Image, ImageTk
import speech_recognition as sr
import pyttsx3
from googletrans import Translator

# Load necessary data and model
lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_simplilearnmodel.h5')

# Initialize the text-to-speech engine
engine = pyttsx3.init()

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

def get_response(intents_list, intents_json, bot_response_image=None):
    if not intents_list:
        # If no intents were predicted, show an error message
        chat_display.image_create(tk.END, image=default_bot_response_image)
        chat_display.insert(tk.END, "Bye ! See you Later\n", "error_message")
        chat_display.tag_add("error_message", "end-2c", "end")  # Align to the left
        return ""

    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            response = random.choice(i['responses'])
            break

    # Display bot response in the chat with provided image on the left side
    if bot_response_image:
        chat_display.image_create(tk.END, image=bot_response_image)
    else:
        chat_display.image_create(tk.END, image=default_bot_response_image)
    
    # Check if response has new line character
    if '\n' in response:
        response_lines = response.split('\n')
        for line in response_lines:
            chat_display.insert(tk.END, " " + line + "\n", "bot_message")
            chat_display.tag_add("bot_message", "end-2c", "end")  # Align to the left
    else:
        chat_display.insert(tk.END, " " + response + "\n", "bot_message")
        chat_display.tag_add("bot_message", "end-2c", "end")  # Align to the left

    # Delay before speaking the bot response
    root.after(500, lambda: speak_response(response))

    return response

def speak_response(response):
    # Speak the bot response
    engine.say(response)
    engine.runAndWait()

def display_user_input(user_input):
    # Display user input in the chat with user image on the right side
    chat_display.image_create(tk.END, image=user_image)
    chat_display.insert(tk.END, "" + user_input + "\n", "user_message")
    chat_display.tag_add("user_message", "end-2c", "end")  # Align to the right

# Bind the Enter key to the send_message function
def send_message(event=None):
    # Get user input
    user_input = entry_field.get()

    if user_input:
        # Use the function to display user input with image
        display_user_input(user_input)

        # Check if the user wants to exit
        if "exit" in user_input.lower() or "bye" in user_input.lower():
            # Display bot response in the chat with default bot response image
            get_response([], {}, default_bot_response_image)
            # Schedule termination after 2 seconds
            root.after(2000, terminate_program)
        else:
            # Check if the user input matches any pattern in the intents file
            matched_pattern = False
            for intent in intents['intents']:
                for pattern in intent['patterns']:
                    if pattern.lower() in user_input.lower():
                        matched_pattern = True
                        break
                if matched_pattern:
                    break

            if not matched_pattern:
                # If no pattern is matched, show an error message
                chat_display.image_create(tk.END, image=default_bot_response_image)
                chat_display.insert(tk.END, "Error - Input does not match.\n", "error_message")
                chat_display.tag_add("error_message", "end-2c", "end")  # Align to the left
            else:
                # Get chatbot response
                intents_list = predict_class(user_input)

                # Get chatbot response
                get_response(intents_list, intents)

        # Automatically scroll to the bottom
        chat_display.yview(tk.END)

        # Clear the entry field
        entry_field.delete(0, tk.END)

# Function to start listening
def start_listening():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        entry_field.delete(0, tk.END)
        entry_field.insert(tk.END, "Listening...")
        entry_field.update()  # Update the entry field to immediately show "Listening..."
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            entry_field.delete(0, tk.END)
            entry_field.insert(tk.END, "Recognizing...")
            entry_field.update()  # Update the entry field to immediately show "Recognizing..."
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language='hi-IN')  # Recognize Hindi speech
            translator = Translator()
            translated_query = translator.translate(query, src='hi', dest='en').text  # Translate Hindi to English
            entry_field.delete(0, tk.END)
            entry_field.insert(tk.END, translated_query)
            entry_field.focus_set()
            send_message()  # Automatically send the translated text to chat
        except sr.WaitTimeoutError:
            entry_field.delete(0, tk.END)
            entry_field.insert(tk.END, "Microphone timed out")
            entry_field.update()  # Update the entry field to immediately show "Microphone timed out"
            print("Microphone timed out")
        except sr.UnknownValueError:
            entry_field.delete(0, tk.END)
            entry_field.insert(tk.END, "Could not understand audio")
            entry_field.update()  # Update the entry field to immediately show "Could not understand audio"
            print("Could not understand audio")
        except sr.RequestError as e:
            entry_field.delete(0, tk.END)
            entry_field.insert(tk.END, f"Could not request results; {e}")
            entry_field.update()  # Update the entry field to immediately show the error message
            print(f"Could not request results; {e}")

# Exit the program
def terminate_program():
    root.destroy()  # Close the Tkinter window and terminate the program

# Create a Tkinter window
root = tk.Tk()
root.title("FALCON CHATBOT")

# Load your logo image
pil_image = Image.open("C:\\Users\\kumar\\Desktop\\finalproject\\logo.png")
desired_width = 100
desired_height = 150
pil_image.thumbnail((desired_width, desired_height))

# Create a PhotoImage object for the logo with resized dimensions
logo_image = ImageTk.PhotoImage(pil_image)

# Load user image
user_image_path = "C:\\Users\\kumar\\Desktop\\finalproject\\user_image.jpg"  # Replace with the actual path to your user image
pil_user_image = Image.open(user_image_path)
desired_width_user = 50  # Adjust the desired width of the user image
desired_height_user = 75  # Adjust the desired height of the user image
pil_user_image.thumbnail((desired_width_user, desired_height_user))

# Create a PhotoImage object for the user image with resized dimensions
user_image = ImageTk.PhotoImage(pil_user_image)

# Load default bot response image
pil_default_bot_response_image = Image.open("C:\\Users\\kumar\\Desktop\\finalproject\\chatbot\\logo.png")  # Replace with the path to your default bot response image
pil_default_bot_response_image.thumbnail((desired_width // 2, desired_height // 2))  # Decrease the size
default_bot_response_image = ImageTk.PhotoImage(pil_default_bot_response_image)

# Create a label for the logo
logo_label = tk.Label(root, image=logo_image)
logo_label.grid(row=0, column=0, sticky="n", padx=10, pady=10)

# Add the text "HEALTHMATE" below the logo
healthmate_label = tk.Label(root, text="HEALTHMATE", font=("Helvetica", 16, "bold"))
healthmate_label.grid(row=1, column=0, sticky="n", padx=10, pady=5)

# Create a text widget for displaying the chat with increased font size and boldness
chat_display = tk.Text(root, wrap=tk.WORD, width=50, height=20, font=("Helvetica", 12, "bold"))
chat_display.grid(row=2, column=0, padx=20, pady=10, columnspan=4)  # Set columnspan to 4 to occupy four columns
chat_display.config(spacing1=0, spacing2=0)  # Ensure subsequent lines start from the beginning

# Create an entry widget for user input with increased font size and boldness
entry_field = tk.Entry(root, width=40, font=("Helvetica", 12, "bold"))
entry_field.grid(row=3, column=0, padx=30, pady=15, columnspan=2)  # Set columnspan to 2 to occupy two columns
# Bind the Enter key to the send_message function
entry_field.bind("<Return>", send_message)

# Create a button to send messages
send_button = tk.Button(root, text="Send", command=send_message, font=("Helvetica", 12, "bold"))
send_button.grid(row=3, column=2, padx=(0, 10), pady=15)  # Adjust padx to create space between entry_field and send_button

# Load the microphone image
mic_image = Image.open("C:\\Users\\kumar\\Desktop\\finalproject\\mic.jpg")  # Replace "mic.jpg" with the path to your microphone image
mic_image = mic_image.resize((30, 30))
mic_icon = ImageTk.PhotoImage(mic_image)

# Create a button to use microphone
mic_button = tk.Button(root, image=mic_icon, command=start_listening)
mic_button.grid(row=3, column=3, padx=10, pady=15)  # Place the mic_button in column 3

# Configure tags for user and bot messages
chat_display.tag_configure("user_message", foreground="green", justify='left')
chat_display.tag_configure("bot_message", foreground="black", justify='left')
chat_display.tag_configure("error_message", foreground="red", justify='left')

# Run the Tkinter main loop
root.mainloop()
