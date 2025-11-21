from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import subprocess, uuid, os

app = FastAPI(title="Universal Video Downloader", version="3.0")

DOWNLOAD_DIR = Path("/downloads")
COOKIE_DIR = Path("/app/cookies")

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def detect_type(url: str):
    url = url.lower()

    if "instagram.com/stories/" in url:
        return "ig_story"

    if "instagram.com/reel/" in url:
        return "ig_reel"

    if "instagram.com/p/" in url:
        return "ig_post"

    if "/story/" in url and "tiktok" in url:
        return "tiktok_story"

    if "tiktok.com" in url:
        return "tiktok"

    if "youtube.com/shorts" in url or "youtu.be/shorts" in url:
        return "yt_shorts"

    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"

    return "generic"


def select_cookie(url_type: str):
    if url_type in ["ig_story", "ig_reel", "ig_post"]:
        return COOKIE_DIR / "instagram.txt"

    if url_type in ["tiktok", "tiktok_story"]:
        return COOKIE_DIR / "tiktok.txt"

    if url_type in ["youtube", "yt_shorts"]:
        youtube_cookie = COOKIE_DIR / "youtube.txt"
        fallback_cookie = COOKIE_DIR / "cookies.txt"
        if youtube_cookie.exists():
            return youtube_cookie
        if fallback_cookie.exists():
            return fallback_cookie

    return None


def run_command(cmd: list[str]):
    try:
        return subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        detail = e.stderr or e.stdout or str(e)
        raise HTTPException(status_code=500, detail=detail)


def get_new_download(before: set[str]) -> Path:
    after = set(os.listdir(DOWNLOAD_DIR))
    new_files = sorted(after - before)

    if not new_files:
        raise HTTPException(status_code=500, detail="Falha ao localizar o arquivo baixado")

    return DOWNLOAD_DIR / new_files[0]


def ensure_mp4(source: Path) -> Path:
    if source.suffix.lower() == ".mp4":
        return source

    target = source.with_suffix(".mp4")
    run_command(["ffmpeg", "-y", "-i", str(source), "-c", "copy", str(target)])

    if target.exists() and target != source:
        source.unlink(missing_ok=True)

    return target


@app.post("/download")
def download(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL inválida")

    url_type = detect_type(url)
    cookie_file = select_cookie(url_type)
    before_download = set(os.listdir(DOWNLOAD_DIR))

    if url_type == "ig_story":
        cmd = ["gallery-dl", "-d", str(DOWNLOAD_DIR)]

        if cookie_file and cookie_file.exists():
            cmd += ["--cookies", str(cookie_file)]

        cmd.append(url)
        run_command(cmd)

        final_file = ensure_mp4(get_new_download(before_download))
        return {"status": "ok", "file": final_file.name, "download_url": f"/file/{final_file.name}"}

    if url_type == "tiktok_story":
        cmd = ["gallery-dl", "-d", str(DOWNLOAD_DIR)]

        if cookie_file and cookie_file.exists():
            cmd += ["--cookies", str(cookie_file)]

        cmd.append(url)
        run_command(cmd)

        final_file = ensure_mp4(get_new_download(before_download))
        return {"status": "ok", "file": final_file.name, "download_url": f"/file/{final_file.name}"}

    filename = str(uuid.uuid4())
    output_path_template = str(DOWNLOAD_DIR / f"{filename}.%(ext)s")

    cmd = [
        "yt-dlp",
        "--force-ipv4",
        "--geo-bypass",
        "--no-check-certificates",
        "--concurrent-fragments",
        "10",
        "--retries",
        "5",
        "--fragment-retries",
        "5",
        "--merge-output-format",
        "mp4",
        "--format",
        "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
        "--user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "-o",
        output_path_template,
    ]

    if cookie_file and cookie_file.exists():
        cmd += ["--cookies", str(cookie_file)]

    cmd.append(url)

    run_command(cmd)

    final_file = ensure_mp4(get_new_download(before_download))
    return {"status": "ok", "file": final_file.name, "download_url": f"/file/{final_file.name}"}


@app.get("/file/{filename}")
def get_file(filename: str):
    path = DOWNLOAD_DIR / filename

    if not path.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    return FileResponse(path, filename=filename)
