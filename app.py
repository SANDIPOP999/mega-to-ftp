import os
import time
from mega import Mega
from ftplib import FTP
from fastapi import FastAPI, Form
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# FTP credentials from environment variables
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_PATH = os.getenv("FTP_PATH")

# Retry logic for FTP upload
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

# Define Pydantic model for the form data
class FileUploadRequest(BaseModel):
    mega_url: str

# Route to serve the landing page (HTML form)
@app.get("/", response_class=HTMLResponse)
async def index():
    with open("index.html") as f:
        return f.read()

# Route to handle the upload
@app.post("/upload")
async def upload(request: FileUploadRequest):
    mega_url = request.mega_url

    # Generate local file path from Mega URL
    file_name = mega_url.split("/")[-1]
    local_file_path = f"./downloads/{file_name}"

    # Download file from Mega and upload to FTP
    download_and_upload_file(mega_url, local_file_path)

    return {"message": "File successfully uploaded!"}
