FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ffmpeg \
      wget \
      curl \
      ca-certificates \
      git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade --no-cache-dir pip && \
    pip install --no-cache-dir -r requirements.txt

COPY server.py /app/server.py
COPY cookies /app/cookies

RUN mkdir -p /downloads

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
