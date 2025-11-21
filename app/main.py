
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import subprocess, os, uuid, mimetypes, json

app = FastAPI(title="YouTube Auto MP4 Downloader", version="2.0")

DOWNLOAD_DIR = "/downloads"
COOKIES = "/app/cookies/youtube.txt"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    url: str

def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return r.stdout
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, detail=e.stderr or str(e))

@app.post("/download")
def download(req: DownloadRequest):
    url = req.url
    uid = str(uuid.uuid4())
    out = f"{DOWNLOAD_DIR}/{uid}.%(ext)s"

    cmd = [
        "yt-dlp",
        "--cookies", COOKIES,
        "--no-playlist",
        "--force-ipv4",
        "--geo-bypass",
        "--no-check-certificates",

        # JS Challenge solver (Node.js)
        "--execjs",

        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--extractor-args", "youtube:player_client=android",

        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--force-overwrites",

        "-o", out,
        url
    ]

    run(cmd)

    # Locate output file
    files = os.listdir(DOWNLOAD_DIR)
    fn = next((f for f in files if f.startswith(uid)), None)
    if not fn:
        raise HTTPException(500, "Falha ao baixar vídeo (nenhum arquivo encontrado).")

    path = f"{DOWNLOAD_DIR}/{fn}"
    mime, _ = mimetypes.guess_type(path)
    if not mime: mime = "video/mp4"

    with open(path, "rb") as f:
        data = f.read()
    os.remove(path)

    return Response(content=data, media_type=mime)

@app.get("/")
def root():
    return {"status": "ok", "version": "2.0", "mode": "nodejs_auto_best_mp4"}
