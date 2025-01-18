import os
from flask import Flask, request, jsonify
from mega import Mega
from ftplib import FTP
import tempfile
import shutil
from megadown import Mega as MegaDown

app = Flask(__name__)

# FTP credentials
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

# Mega client initialization
mega = MegaDown()


@app.route('/download_and_upload', methods=['POST'])
def download_and_upload():
    mega_url = request.form.get('mega_url')
    
    if not mega_url:
        return jsonify({"error": "MEGA URL is required"}), 400
    
    # Download file from MEGA
    temp_dir = tempfile.mkdtemp()
    file_path = mega.download(mega_url, temp_dir)

    if not file_path:
        return jsonify({"error": "Failed to download file from MEGA"}), 500

    # Generate the file path for FTP upload
    filename = os.path.basename(file_path)
    remote_path = generate_ftp_path(filename)

    # Upload the file to FTP
    try:
        upload_to_ftp(file_path, remote_path)
        return jsonify({"message": f"File uploaded successfully to {remote_path}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


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
