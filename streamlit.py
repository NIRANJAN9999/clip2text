import streamlit as st
import yt_dlp
import os
import subprocess
import random
import string
import whisper
import tempfile
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.auth.transport.requests

# Ensure the uploads folder exists
output_folder = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Load the Whisper tiny model
model = whisper.load_model("tiny")

# Scopes for YouTube API access
SCOPES = ['https://www.googleapis.com/auth/youtube']

# Generate a new filename based on the first 5 characters and 5 random digits
def generate_new_filename(original_filename):
    base_name = original_filename[:5]  # First 5 characters
    random_digits = ''.join(random.choices(string.digits, k=5))  # 5 random digits
    new_filename = f"{base_name}_{random_digits}.wav"
    return new_filename

# Download the audio from the URL using yt-dlp with OAuth
def download_audio(url, credentials):
    # Create a session with the credentials
    session = google.auth.transport.requests.AuthorizedSession(credentials)
    
    # Note: This is a placeholder since yt-dlp doesn't support OAuth directly
    temp_cookie_path = os.path.join(tempfile.gettempdir(), 'dummy_cookies.txt')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'cookiefile': temp_cookie_path
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            original_audio_title = info_dict.get('title', 'audio')
            audio_extension = info_dict.get('ext', 'webm')
    except yt_dlp.utils.DownloadError as e:
        raise Exception(f"Failed to download video: {str(e)}")
    
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
    command = ['ffmpeg', '-i', input_path, '-acodec', 'pcm_s16le', '-ar', '44100', output_path]

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        raise Exception(f"ffmpeg command failed: {result.stderr}")

    # Optionally remove the original file if needed
    os.remove(input_path)

# Function to transcribe audio using Whisper
def transcribe_audio(audio_path):
    try:
        result = model.transcribe(audio_path)
        return result['text']
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")

# Streamlit UI
st.title('YouTube Video Transcription')

# Debug: Print out the secrets to verify they're loaded correctly
st.write("Debugging Secrets:")
st.write(st.secrets["google_oauth_credentials"])

# OAuth Flow
def run_oauth_flow():
    try:
        # Use Streamlit secrets to get the credentials
        flow = Flow.from_client_config(
            client_config=st.secrets["google_oauth_credentials"],
            scopes=SCOPES,
            redirect_uri=st.secrets["google_oauth_credentials"]["redirect_uris"][0]
        )
        
        # Generate URL for OAuth consent
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        # Display the URL to the user
        st.write("Please visit this URL to authorize access:")
        st.write(auth_url)
        
        # Get the authorization code from the user
        code = st.text_input('Enter the authorization code from the URL:')
        
        if st.button('Authorize'):
            flow.fetch_token(code=code)
            credentials = flow.credentials
            return credentials
    except Exception as e:
        st.error(f"OAuth flow error: {str(e)}")
        return None

# Check if we have credentials
if 'credentials' not in st.session_state or st.session_state['credentials'] is None:
    st.subheader('Step 1: Login with Google')
    credentials = run_oauth_flow()
    if credentials:
        st.session_state['credentials'] = credentials
        st.success('Login successful! You can now proceed to Step 2.')
else:
    # Input for video URL
    st.subheader('Step 2: Enter YouTube Video URL')
    video_url = st.text_input('Enter YouTube Video URL')

    if st.button('Transcribe'):
        if video_url:
            with st.spinner('Downloading and transcribing video...'):
                try:
                    # Step 1: Download and convert the audio
                    audio_file_path = download_audio(video_url, st.session_state['credentials'])
                    
                    # Step 2: Transcribe the audio using Whisper
                    transcription = transcribe_audio(audio_file_path)
                    
                    st.write("Transcription:")
                    st.write(transcription)
                except Exception as e:
                    st.error(f'An error occurred: {str(e)}')
        else:
            st.warning('Please enter a YouTube video URL.')
