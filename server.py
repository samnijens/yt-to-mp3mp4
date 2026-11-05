"""Kleine lokale server voor index.html.

Installeren:  pip install flask yt-dlp
Ook nodig:    ffmpeg (https://ffmpeg.org) voor mp3-conversie
Starten:      python server.py   ->   open http://localhost:5000
"""
import os, tempfile, shutil
from flask import Flask, request, send_file, send_from_directory, jsonify
import yt_dlp

app = Flask(__name__)
HERE = os.path.dirname(os.path.abspath(__file__))


@app.get("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.post("/convert")
def convert():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    fmt = data.get("format", "mp3")
    if not url.startswith(("https://www.youtube.com/", "https://youtube.com/",
                           "https://youtu.be/", "https://m.youtube.com/",
                           "https://music.youtube.com/")):
        return jsonify(error="Dat is geen geldige YouTube-link."), 400

    tmp = tempfile.mkdtemp()
    opts = {"outtmpl": os.path.join(tmp, "%(title).150B.%(ext)s"),
            "noplaylist": True, "quiet": True}
    if fmt == "mp3":
        opts.update(format="bestaudio/best", postprocessors=[
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
             "preferredquality": "192"}])
    else:
        opts.update(format="bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                    merge_output_format="mp4")
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        path = os.path.join(tmp, os.listdir(tmp)[0])
        resp = send_file(path, as_attachment=True)
        resp.call_on_close(lambda: shutil.rmtree(tmp, ignore_errors=True))
        return resp
    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        return jsonify(error=f"Omzetten mislukt: {e}"), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
