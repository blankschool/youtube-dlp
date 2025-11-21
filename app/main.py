
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import subprocess, os, uuid, mimetypes

app = FastAPI(title="YouTube Auto MP4 Downloader", version="3.0")

DOWNLOAD_DIR = "/downloads"
COOKIES = "/app/cookies/youtube.txt"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    url: str

def run(cmd):
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, detail=(e.stderr or e.stdout))

@app.post("/download")
def download(req: DownloadRequest):
        uid = str(uuid.uuid4())
        out = f"{DOWNLOAD_DIR}/{uid}.%(ext)s"

        cmd = [
            "yt-dlp",
            "--cookies", COOKIES,
            "--no-playlist",
            "--force-ipv4",
            "--no-check-certificates",
            "--geo-bypass",
            "--compat-options", "all",
            "--extractor-args", "youtube:player_client=android",
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "--force-overwrites",
            "-o", out,
            req.url
        ]

        run(cmd)

        files = os.listdir(DOWNLOAD_DIR)
        fn = next((f for f in files if f.startswith(uid)), None)
        if not fn:
            raise HTTPException(500, "Nenhum arquivo gerado pelo yt-dlp.")

        path = f"{DOWNLOAD_DIR}/{fn}"
        mime = mimetypes.guess_type(path)[0] or "video/mp4"

        with open(path, "rb") as f:
            data = f.read()

        os.remove(path)

        return Response(content=data, media_type=mime)

@app.get("/")
def root():
    return {"status": "ok", "version": "3.0", "mode": "auto_best_mp4"}
