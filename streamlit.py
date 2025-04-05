import streamlit as st
import yt_dlp
import os
import subprocess
import random
import string
import whisper

# Ensure the uploads folder exists
output_folder = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Load the Whisper tiny model
model = whisper.load_model("tiny")

# Generate a new filename based on the first 5 characters and 5 random digits
def generate_new_filename(original_filename):
    base_name = original_filename[:5]  # First 5 characters
    random_digits = ''.join(random.choices(string.digits, k=5))  # 5 random digits
    new_filename = f"{base_name}_{random_digits}.wav"
    return new_filename

# List of User-Agent strings
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    # Add more user agents as needed
]

# Download the audio from the URL using yt-dlp with User-Agent rotation
def download_audio(url):
    # Randomly select a User-Agent
    user_agent = random.choice(user_agents)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'User-Agent': user_agent  # Add this line to rotate User-Agent
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        original_audio_title = info_dict.get('title', 'audio')
        audio_extension = info_dict.get('ext', 'webm')
    
    # Path to the downloaded audio file
    downloaded_audio_path = os.path.join(output_folder, f"{original_audio_title}.{audio_extension}")
    
    # Step 1: Convert to .wav and rename
    new_filename = generate_new_filename(original_audio_title)
    wav_path = os.path.join(output_folder, new_filename)

    # Convert and rename to .wav
    convert_to_wav(downloaded_audio_path, wav_path)
    
    return wav_path  # Return the final .wav file path

# Convert the file to .wav format
def convert_to_wav(input_path, output_path):
    command = ['ffmpeg', '-i', input_path, output_path]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise Exception(f"ffmpeg command failed: {result.stderr.decode()}")

    # Optionally remove the original file if needed
    os.remove(input_path)

# Function to transcribe audio using Whisper
def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result['text']

# Streamlit UI
st.title('YouTube Video Transcription')

# Input for video URL
video_url = st.text_input('Enter YouTube Video URL')

if st.button('Transcribe'):
    if video_url:
        try:
            # Step 1: Download and convert the audio
            audio_file_path = download_audio(video_url)
            
            # Step 2: Transcribe the audio using Whisper
            transcription = transcribe_audio(audio_file_path)
            
            st.write("Transcription:")
            st.write(transcription)
        except Exception as e:
            st.error(f'An error occurred: {str(e)}')
    else:
        st.warning('Please enter a YouTube video URL.')
