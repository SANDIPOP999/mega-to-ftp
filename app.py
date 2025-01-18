import os
import requests
import time
from flask import Flask, request, jsonify
from mega import Mega
from ftplib import FTP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# FTP credentials from environment variables
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_PATH = os.getenv("FTP_PATH")

# Retry logic for FTP upload (without tenacity)
def upload_file_with_retry(local_file_path, retries=5, delay=2):
    attempt = 0
    while attempt < retries:
        try:
            with FTP(FTP_HOST) as ftp:
                ftp.login(FTP_USER, FTP_PASS)
                with open(local_file_path, "rb") as file:
                    ftp.cwd(FTP_PATH)
                    ftp.storbinary(f"STOR {os.path.basename(local_file_path)}", file)
            print("Upload successful!")
            break
        except Exception as e:
            attempt += 1
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("All attempts failed.")

# Download Mega file and upload to FTP
def download_and_upload_file(mega_url, local_file_path):
    # Initialize Mega API
    mega = Mega()
    m = mega.login()  # Log in anonymously

    # Download file from Mega
    print(f"Downloading file from Mega: {mega_url}")
    file = m.download_url(mega_url, local_file_path)
    print(f"File downloaded: {file}")

    # Upload to FTP
    upload_file_with_retry(local_file_path)

@app.route('/')
def index():
    return open('index.html').read()

@app.route('/upload', methods=['POST'])
def upload():
    mega_url = request.form['mega_url']

    # Generate local file path from Mega URL
    file_name = mega_url.split("/")[-1]
    local_file_path = f"./downloads/{file_name}"

    # Download file from Mega and upload to FTP
    download_and_upload_file(mega_url, local_file_path)
    
    return jsonify({"message": "File successfully uploaded!"})

if __name__ == "__main__":
    app.run(debug=True)
