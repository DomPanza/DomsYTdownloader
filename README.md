# Dom's YouTube Downloader

A personal project built to have a cleaner, ad-free way to download YouTube videos 
and audio — no shady redirect sites, no fake "download" buttons, no popups.

Built with Python, Flask, yt-dlp, and ffmpeg.

An attempt was made to host this publicly via GitHub Pages, but GitHub Pages only 
supports static sites and can't run the Python backend this project needs. So for 
now, this needs to be downloaded and run locally — instructions below.

## Features

- Paste a YouTube URL and download as MP4 (4K / 1080p / 720p / 480p) or MP3
- Live download progress (percent, speed, ETA)
- No files stored on the server after download — everything is cleaned up automatically

## Requirements

- Python 3.10+
- ffmpeg (bundled in the `ffmpeg/` folder — no separate install needed)

## Setup

1. Clone this repo through the top code option

2. Create and activate a virtual environment:
python -m venv venv
venv\Scripts\activate # Windows
source venv/bin/activate # Mac/Linux


3. Install dependencies:
pip install -r requirements.txt


4. Run the app:
python main.py


5. Open `http://127.0.0.1:5000/` in your browser.

## Notes

This was built as a learning project and for personal use. Downloading YouTube 
content may be subject to YouTube's Terms of Service depending on how it's used — 
this tool is intended for personal/offline use of content you have the right to download.
