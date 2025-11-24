FROM node:16-slim

ARG DEBIAN_FRONTEND=noninteractive

# Fix APT sources for older Debian-based images (like node:16-slim)
RUN sed -i 's|deb.debian.org/debian|archive.debian.org/debian|g' /etc/apt/sources.list \
    && sed -i 's|security.debian.org/debian-security|archive.debian.org/debian-security|g' /etc/apt/sources.list \
    && sed -i '/deb .*stretch-updates/d' /etc/apt/sources.list || true

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        ffmpeg \
        ca-certificates \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir yt-dlp

WORKDIR /app

COPY backend /app
COPY appdata /app/appdata
COPY public /app/public

# pm2-runtime is required by the backend's start script
RUN npm install -g pm2 \
    && npm install

EXPOSE 17442

CMD ["npm", "start"]
