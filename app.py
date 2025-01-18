import os
from flask import Flask, request, jsonify
from mega import Mega
from ftplib import FTP
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__)

# FTP Credentials (from .env file)
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')
FTP_PATH = os.getenv('FTP_PATH')

# Initialize Mega (no login required for public files)
mega = Mega()

# Route for receiving Mega URL
@app.route('/upload', methods=['POST'])
def upload_file():
    # Get the Mega URL from the form
    mega_url = request.form.get('mega_url')
    if not mega_url:
        return jsonify({'message': 'Mega URL is required'}), 400

    # Get the file name from the URL
    file_name = mega_url.split('/')[-1]  # Extract the file name from the URL (e.g., sakomoto-days-s1-ep1.mp4)

    # Download the file from Mega
    file_path = download_from_mega(mega_url, file_name)
    
    # Rename the file if necessary (you can customize this logic)
    renamed_file_path = rename_file(file_path)
    
    # Generate FTP path based on file name (e.g., sakomoto-days/s1/)
    ftp_path = generate_ftp_path(file_name)
    
    # Upload the file to FTP
    try:
        upload_to_ftp(renamed_file_path, ftp_path)
        return jsonify({'message': 'File uploaded successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

# Function to download file from Mega using a public link
def download_from_mega(url, file_name):
    # Download file using Mega.py (public file URL)
    file = mega.download(url, dest_path='./downloads')  # Save to the local 'downloads' folder
    return f'./downloads/{file_name}'

# Function to rename file if needed
def rename_file(file_path):
    # Example: Rename file (you can customize this logic)
    new_name = f'new_{os.path.basename(file_path)}'
    new_path = os.path.join(os.path.dirname(file_path), new_name)
    os.rename(file_path, new_path)
    return new_path

# Function to generate FTP path based on file name
def generate_ftp_path(file_name):
    # Extract information from the file name (example: sakomoto-days-s1-ep1.mp4 -> sakomoto-days/s1/)
    match = re.match(r"([a-zA-Z0-9-]+)-s(\d+)-ep(\d+)\.mp4", file_name)
    if match:
        series_name = match.group(1)
        season = match.group(2)
        return f'{series_name}/s{season}/'
    return "uploads/"  # Default path if regex does not match

# Function to upload file to FTP
def upload_to_ftp(file_path, ftp_path):
    # FTP upload logic
    with FTP(FTP_HOST) as ftp:
        ftp.login(user=FTP_USER, passwd=FTP_PASS)
        ftp.cwd(ftp_path)  # Change to the target directory
        with open(file_path, 'rb') as f:
            ftp.storbinary(f"STOR {os.path.basename(file_path)}", f)
    print(f"Successfully uploaded {file_path} to FTP server at {ftp_path}")

if __name__ == '__main__':
    app.run(debug=True)
