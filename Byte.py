import speech_recognition as sr
import pyttsx3
import wikipedia
import cv2
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime
import threading
import requests
import json
import time

# Initialize Spotipy client
client_credentials_manager = SpotifyClientCredentials(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Initialize the speech recognizer and engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Function to speak out the response
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen to the user's voice command asynchronously
def listen(callback):
    def listen_thread():
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

            try:
                print("Recognizing...")
                command = recognizer.recognize_google(audio)
                print("User said:", command)
                callback(command.lower())
            except sr.UnknownValueError:
                print("Sorry, I didn't catch that.")
                callback("")
            except sr.RequestError as e:
                print("Could not request results; {0}".format(e))
                callback("")

    threading.Thread(target=listen_thread).start()

# Function to perform Wikipedia search with caching
wiki_cache = {}
def perform_wikipedia_search(query):
    if query in wiki_cache:
        speak(wiki_cache[query])
    else:
        try:
            result = wikipedia.summary(query, sentences=2)
            wiki_cache[query] = result
            speak(result)
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError) as e:
            speak("Sorry, I couldn't find any information on that topic.")
        except Exception as e:
            speak("An error occurred while searching for the topic.")

# Function to capture photo from webcam
def take_photo():
    try:
        camera = cv2.VideoCapture(0)
        return_value, image = camera.read()
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
        cv2.imwrite(filename, image)
        camera.release()
        speak("Photo captured successfully!")
    except Exception as e:
        speak("Sorry, I couldn't capture the photo.")

# Function to record video from webcam
def record_video():
    try:
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".avi"
        camera = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

        while True:
            ret, frame = camera.read()
            out.write(frame)
            cv2.imshow('Recording...', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break  # Stop recording if 'q' is pressed

        camera.release()
        out.release()
        cv2.destroyAllWindows()
        speak("Recording stopped.")
    except Exception as e:
        speak("Sorry, I couldn't record the video.")

# Function to play music from Spotify
def play_music(song_name):
    try:
        results = sp.search(q=song_name, type='track', limit=1)
        if results['tracks']['items']:
            track_uri = results['tracks']['items'][0]['uri']
            sp.start_playback(uris=[track_uri])
            speak(f"Now playing {song_name}.")
        else:
            speak(f"Sorry, I couldn't find the song {song_name}.")
    except Exception as e:
        speak("Sorry, I couldn't play the music.")

# Function to fetch news from News API
def get_news(category):
    try:
        news_api_key = 'a2ec36c87ac54c5d89064f131bf9af64'  # Dummy API key
        url = f'https://newsapi.org/v2/top-headlines?category={category}&apiKey={news_api_key}'
        response = requests.get(url)
        news_data = json.loads(response.text)
        articles = news_data['articles']
        if articles:
            for article in articles:
                speak(article['title'])
                speak(article['description'])
        else:
            speak("Sorry, no news articles available for this category.")
    except Exception as e:
        speak("Sorry, I couldn't fetch the news.")

# Function to add a reminder
def add_reminder(reminder, time_str):
    try:
        reminder_time = datetime.strptime(time_str, '%I:%M %p')
        current_time = datetime.now()
        if reminder_time < current_time:
            reminder_time = reminder_time.replace(day=current_time.day + 1)
        delta = (reminder_time - current_time).total_seconds()
        timer = threading.Timer(delta, speak, args=[f"Reminder: {reminder}"])
        timer.start()
        speak("Reminder set successfully.")
    except ValueError:
        speak("Invalid time format. Please specify the reminder time in 'hour:minute AM/PM' format, for example, '10:30 AM'.")

# Function to handle user commands
def handle_command(command):
    if "hello" in command:
        speak("Hello there!")
    elif "how are you" in command:
        speak("I'm doing great, thank you!")
    elif "search for" in command:
        query = command.replace("search for", "").strip()
        perform_wikipedia_search(query)
    elif "take a photo" in command:
        take_photo()
    elif "record a video" in command:
        threading.Thread(target=record_video).start()
    elif "play" in command:
        song_name = command.replace("play", "").strip()
        play_music(song_name)
    elif "read today's news" in command:
        speak("Sure, which category of news would you like to hear?")
        category_command = listen_for_news_category()
        categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
        if category_command.lower() in categories:
            speak(f"Reading today's {category_command} news:")
            get_news(category_command.lower())
        else:
            speak("Sorry, that's not a valid category.")
    elif "remind me" in command:
        split_command = command.split("remind me")
        reminder = split_command[1].split("at")[0].strip()
        time_str = split_command[1].split("at")[1].strip()
        add_reminder(reminder, time_str)
    elif "goodbye" in command:
        speak("Goodbye!")
        exit()
    else:
        speak("I'm sorry, I didn't understand that command.")

# Function to listen for news category asynchronously
def listen_for_news_category():
    category_command = ""
    def callback(command):
        nonlocal category_command
        category_command = command

    listen(callback)
    # Wait for command to be received asynchronously
    while not category_command:
        time.sleep(0.1)
    return category_command

# Main function to handle listening loop
def main():
    speak("Hi, I'm your assistant. How can I help you?")
    while True:
        listen(handle_command)

if __name__ == "__main__":
    main()
