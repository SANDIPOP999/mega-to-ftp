import os
from flask import Flask, request, jsonify
from megadown import MegaDown
from ftplib import FTP
import tempfile
import shutil

app = Flask(__name__)

# FTP credentials
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

# Initialize MegaDown client
mega = MegaDown()


@app.route('/download_and_upload', methods=['POST'])
def download_and_upload():
    mega_url = request.form.get('mega_url')
    
    if not mega_url:
        return jsonify({"error": "MEGA URL is required"}), 400
    
    # Download file from MEGA using MegaDown
    try:
        file = mega.download(mega_url)
    except Exception as e:
        return jsonify({"error": f"Failed to download file from MEGA: {str(e)}"}), 500
    
    if not file:
        return jsonify({"error": "Failed to download file from MEGA"}), 500

    # Generate the file path for FTP upload
    filename = os.path.basename(file)
    remote_path = generate_ftp_path(filename)

    # Upload the file to FTP
    try:
        upload_to_ftp(file, remote_path)
        return jsonify({"message": f"File uploaded successfully to {remote_path}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary directory if used
        if os.path.exists(file):
            os.remove(file)


def generate_ftp_path(filename):
    # Extract the base name (like "sakomoto-days-s1-ep1.mp4")
    name_parts = filename.split('-')
    show_name = name_parts[0]
    season = name_parts[1]
    episode = name_parts[2]
    file_name = f"{show_name}/{season}/file/{filename}"
    return file_name


def upload_to_ftp(file_path, remote_path):
    # Connect to FTP server
    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)

    # Open file in binary mode for uploading
    with open(file_path, 'rb') as file:
        ftp.storbinary(f"STOR {remote_path}", file)

    # Close FTP connection
    ftp.quit()


if __name__ == '__main__':
    app.run(debug=True)
