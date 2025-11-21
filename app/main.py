
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import subprocess, os, uuid, json, mimetypes

app = FastAPI(title="YouTube API With Cookies", version="1.1")

DOWNLOAD_DIR = "/downloads"
COOKIES = "/app/cookies/youtube.txt"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class FormatRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_id: str

def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return p.stdout
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, detail=e.stderr or str(e))

@app.post("/formats")
def formats(req: FormatRequest):
    url = req.url

    cmd = [
        "yt-dlp",
        "-J",
        "--cookies", COOKIES,
        "--no-playlist",
        "--skip-download",
        "--force-ipv4",
        "--geo-bypass",
        "--no-check-certificates",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--extractor-args", "youtube:player_client=web",
        url
    ]

    info = json.loads(run(cmd))

    video_formats = []
    audio_formats = []

    for f in info.get("formats", []):
        ext = f.get("ext")
        fmt_id = f.get("format_id")
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        filesize = f.get("filesize") or f.get("filesize_approx")
        res = f.get("resolution")
        fps = f.get("fps")
        size_mb = round(filesize/(1024*1024),2) if filesize else None

        # BEST MP4 ONLY (no webm)
        if ext=="mp4" and vcodec not in (None,"none"):
            label = f"MP4 {res or ''} {fps or ''}fps"
            if size_mb: label += f" (~{size_mb} MB)"
            video_formats.append({
                "format_id": fmt_id,
                "label": label.strip(),
                "resolution": res,
                "fps": fps,
                "filesize": filesize
            })

        # AUDIO BEST (m4a preferred)
        if vcodec in (None,"none") and acodec not in (None,"none"):
            label = f"{ext.upper()} {f.get('abr','')}kbps"
            if size_mb: label += f" (~{size_mb} MB)"
            audio_formats.append({
                "format_id": fmt_id,
                "label": label.strip(),
                "filesize": filesize
            })

    # Sort video's best first
    video_formats.sort(key=lambda x: int(x["resolution"].replace("p","")) if x["resolution"] else 0, reverse=True)

    # Sort audio by bitrate
    audio_formats.sort(key=lambda x: x.get("filesize") or 0, reverse=True)

    return {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "video_formats": video_formats,
        "audio_formats": audio_formats
    }

@app.post("/download")
def download(req: DownloadRequest):
    uid = str(uuid.uuid4())
    out = f"{DOWNLOAD_DIR}/{uid}.%(ext)s"

    cmd = [
        "yt-dlp",
        "--cookies", COOKIES,
        "--no-playlist",
        "--force-overwrites",
        "--force-ipv4",
        "--geo-bypass",
        "--no-check-certificates",
        "--user-agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--extractor-args", "youtube:player_client=web",
        "-f", req.format_id,
        "--merge-output-format", "mp4",
        "-o", out,
        req.url
    ]

    run(cmd)

    files = os.listdir(DOWNLOAD_DIR)
    fn = next((f for f in files if f.startswith(uid)), None)
    if not fn:
        raise HTTPException(500,"Falha no download")

    path = f"{DOWNLOAD_DIR}/{fn}"
    mime,_ = mimetypes.guess_type(path)
    if not mime: mime = "video/mp4"

    with open(path,"rb") as f:
        data = f.read()
    os.remove(path)

    return Response(data, media_type=mime)

@app.get("/")
def root():
    return {"status":"ok","cookie_login":True}
