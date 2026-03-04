import yt_dlp
import imageio_ffmpeg
import os
import re
import uuid
from flask import Response
import time
from flask import Flask, render_template, request, after_this_request, send_file

app = Flask(__name__)

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

downloads_folder = "temp_downloads"
os.makedirs(downloads_folder, exist_ok=True)
download_progress = {"percent": 0}

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', "0%").strip()
        download_progress["percent"] = percent

    elif d['status'] == 'finished':
        download_progress["percent"] = "Download Successfull......"

def download_video(url, quality, audio):

    unique_id = str(uuid.uuid4())
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = clean_filename(info.get("title", "video"))

    server_filename = f"{unique_id}.mp4"
    filepath = os.path.join(downloads_folder, server_filename)
    
    quality_map = {
        "360p": "bestvideo[height<=360]+bestaudio/best",
        "720p": "bestvideo[height<=720]+bestaudio/best",
        "1080p": "bestvideo[height<=1080]+bestaudio/best",
        "4K": "bestvideo[height<=2160]+bestaudio/best",
        "Best (Highest)": "bestvideo+bestaudio/best"
    }

    options = {
        "format": quality_map[quality],
        "ffmpeg_location": ffmpeg_path,
        "merge_output_format": "mp4",
        "outtmpl": filepath,
        "progress_hooks": [progress_hook],
        "noplaylist": True
    }

    if audio == "AAC - Slow":
        options["postprocessor_args"] = ["-c:a", "aac"]
    else:
        options["postprocessor_args"] = ["-c:a", "copy"]

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
    return filepath, title

@app.route("/progress")
def progress():
    def generate():
        while True:
            yield f"data:{download_progress['percent']}\n\n"
            time.sleep(1)

    return Response(generate(), mimetype="text/event-stream")

@app.route("/", methods=["GET", "POST"])
def index():

    message = ""

    if request.method == "POST":

        url = request.form["url"]
        quality = request.form["quality"]
        audio = request.form["audio"]

        filepath,title=download_video(url, quality, audio)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(filepath)
            except Exception:
                pass
            return response

        return send_file(filepath,as_attachment=True, download_name=f"{title}.mp4")

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)