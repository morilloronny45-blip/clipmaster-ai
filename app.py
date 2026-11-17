import os, uuid, subprocess, shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parent
UPLOADS = ROOT / "uploads"
OUTPUTS = ROOT / "outputs"
UPLOADS.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024
ALLOWED = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout or "Error ejecutando FFmpeg")[-1800:])
    return p.stdout

def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    return float(out.strip())

def download_url(url, dest):
    # yt-dlp puede procesar enlaces públicos compatibles; el acceso depende
    # de las reglas y permisos de cada plataforma.
    run(["yt-dlp", "--no-playlist", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
         "-o", str(dest), url])
    candidates = list(dest.parent.glob(dest.stem + ".*"))
    if not candidates:
        raise RuntimeError("No se pudo descargar el video desde ese enlace.")
    return candidates[0]

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/process")
def process():
    job = uuid.uuid4().hex[:10]
    work = UPLOADS / job
    outdir = OUTPUTS / job
    work.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    try:
        url = (request.form.get("url") or "").strip()
        f = request.files.get("video")
        if bool(url) == bool(f and f.filename):
            return jsonify(error="Adjunta un video o pega un enlace, pero no ambos."), 400

        if url:
            source = download_url(url, work / "source.mp4")
        else:
            name = secure_filename(f.filename)
            if Path(name).suffix.lower() not in ALLOWED:
                return jsonify(error="Formato no compatible. Usa MP4, MOV, MKV o WEBM."), 400
            source = work / name
            f.save(source)

        total = duration(source)
        try:
            segment = int(request.form.get("segment", "60"))
        except ValueError:
            segment = 60
        if segment not in (30, 60, 90):
            segment = 60

        clips = []
        start = 0.0
        index = 1
        while start < total:
            length = min(segment, total - start)
            if length < 2:
                break
            filename = f"clip_{index:02d}.mp4"
            target = outdir / filename
            run(["ffmpeg", "-y", "-ss", str(start), "-i", str(source),
                 "-t", str(length), "-map", "0:v:0", "-map", "0:a?",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                 "-c:a", "aac", "-movflags", "+faststart", str(target)])
            clips.append({"name": filename, "url": f"/download/{job}/{filename}",
                          "start": round(start), "duration": round(length)})
            start += segment
            index += 1

        return jsonify(job=job, duration=round(total), clips=clips,
                       note="Cortes consecutivos creados. La selección automática de momentos destacados aún no está incluida.")
    except Exception as e:
        return jsonify(error=str(e)), 400

@app.get("/download/<job>/<path:filename>")
def download(job, filename):
    folder = OUTPUTS / job
    return send_from_directory(folder, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
