import streamlit as st
import yt_dlp
import os
import subprocess
import random
import string
import whisper
import tempfile

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

# Download the audio from the URL using yt-dlp with user-provided cookies
def download_audio(url, cookie_file):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'cookiefile': cookie_file
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

# Step for user to upload cookies
st.subheader('Step 1: Upload Your YouTube Cookies')
cookie_file = st.file_uploader("Upload your YouTube cookies file (exported from your browser)", type=["txt"])

if cookie_file is not None:
    # Save the uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_cookie_path = os.path.join(temp_dir, 'youtube_cookies.txt')
    with open(temp_cookie_path, 'wb') as f:
        f.write(cookie_file.getvalue())
    
    # Input for video URL
    st.subheader('Step 2: Enter YouTube Video URL')
    video_url = st.text_input('Enter YouTube Video URL')

    if st.button('Transcribe'):
        if video_url:
            try:
                # Step 1: Download and convert the audio
                audio_file_path = download_audio(video_url, temp_cookie_path)
                
                # Step 2: Transcribe the audio using Whisper
                transcription = transcribe_audio(audio_file_path)
                
                st.write("Transcription:")
                st.write(transcription)
            except Exception as e:
                st.error(f'An error occurred: {str(e)}')
        else:
            st.warning('Please enter a YouTube video URL.')
else:
    st.info('Please upload your YouTube cookies file to proceed.')
