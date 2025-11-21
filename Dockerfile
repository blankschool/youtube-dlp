
FROM python:3.11-slim

# Install Node.js for yt-dlp JS challenge support
RUN apt update && apt install -y curl ffmpeg ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt install -y nodejs \
    && apt clean

RUN pip install --no-cache-dir fastapi uvicorn yt-dlp

WORKDIR /app
COPY app /app
RUN mkdir -p /downloads

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
