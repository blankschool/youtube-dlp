FROM node:16-slim

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

RUN npm install

EXPOSE 17442

CMD ["npm", "start"]
