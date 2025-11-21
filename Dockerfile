
FROM python:3.11-slim

RUN apt update && apt install -y ffmpeg wget curl ca-certificates && apt clean
RUN pip install --no-cache-dir fastapi uvicorn yt-dlp

WORKDIR /app
COPY app /app
RUN mkdir -p /downloads

EXPOSE 8080

CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8080"]
