###########################################################################################
#? list of all the imports:
#* - flask: for the web server and routing
#* - yt_dlp: for downloading videos from YouTube and other sites
#* - os: for file and path operations
#* - threading: to run downloads in the background
#* - uuid: to generate unique job IDs
#* - tempfile: to create temporary directories for downloads
#* - shutil: to clean up temporary directories after downloads

from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import threading
import uuid
import tempfile
import shutil

###########################################################################################
#? create the Flask app and a dictionary to track download jobs

app = Flask(__name__)

jobs = {}  #! job_id -> {progress info, temp_dir, filename, status}

###########################################################################################
#? open the main index page

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

###########################################################################################
#? kick off a background download job, return a job_id immediately

@app.route("/start-download", methods=["POST"])
def start_download():
    link = request.form["url"]
    quality = request.form.get("quality", "1080p")

    job_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp(prefix="ytdl_")

    jobs[job_id] = {
        "percent": "0%",
        "speed": "N/A",
        "eta": "N/A",
        "status": "downloading",
        "filename": None,
        "temp_dir": temp_dir,
    }

    def progress_hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)

            if total:
                percent = round(downloaded / total * 100, 1)
            else:
                percent = 0

            speed = d.get('speed')  # bytes per second, or None
            eta = d.get('eta')      # seconds, or None

            jobs[job_id]["percent"] = f"{percent}%"
            jobs[job_id]["speed"] = f"{speed / 1024 / 1024:.2f} MiB/s" if speed else "N/A"
            jobs[job_id]["eta"] = f"{eta}s" if eta is not None else "N/A"

        elif d['status'] == 'finished':
            jobs[job_id]["percent"] = "100%"

    def run_download():
        ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg")
        format_map = {
            "4k": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        }

        try:
            if quality == "mp3":
                ydl_opts = {
                    "outtmpl": os.path.join(temp_dir, f"%(title)s.%(ext)s"),
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                    "ffmpeg_location": ffmpeg_path,
                    "progress_hooks": [progress_hook],
                    "overwrites": True,
                }
            else:
                ydl_opts = {
                    "outtmpl": os.path.join(temp_dir, f"%(title)s.%(ext)s"),
                    "format": format_map.get(quality, format_map["1080p"]),
                    "merge_output_format": "mp4",
                    "ffmpeg_location": ffmpeg_path,
                    "progress_hooks": [progress_hook],
                    "overwrites": True,
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                ext = "mp3" if quality == "mp3" else "mp4"
                filename = base + "." + ext

            jobs[job_id]["filename"] = filename
            jobs[job_id]["status"] = "complete"

        except Exception as e:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(e)

    thread = threading.Thread(target=run_download)
    thread.start()

    return jsonify({"job_id": job_id})

###########################################################################################
#? poll this to check progress on a job

@app.route("/progress/<job_id>")
def progress(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"status": "unknown"})
    return jsonify({
        "percent": job["percent"],
        "speed": job["speed"],
        "eta": job["eta"],
        "status": job["status"],
        "error": job.get("error"),
    })

###########################################################################################
#? once complete, fetch the actual file and clean up the temp folder

@app.route("/fetch-file/<job_id>")
def fetch_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "complete":
        return "Not ready", 400

    filename = job["filename"]
    temp_dir = job["temp_dir"]

    response = send_file(filename, as_attachment=True, download_name=os.path.basename(filename))

    @response.call_on_close
    def cleanup():
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except OSError:
            pass
        jobs.pop(job_id, None)

    return response

###########################################################################################
#? just a general starter route to run the app

if __name__ == "__main__":
    app.run(debug=True, threaded=True)