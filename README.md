# Universal Video Downloader

API em FastAPI para baixar vídeos de Instagram, TikTok e YouTube, sempre entregando MP4 e preparado para rodar via Docker.

## Executando rapidamente
- `docker compose up --build` vai gerar a imagem, montar `./downloads` no host e subir na porta 8080.
- Cookies ficam em `./cookies` (montado como somente leitura). Ajuste os arquivos `instagram.txt` e `tiktok.txt` se precisar de sessões válidas.
- Para YouTube, coloque `youtube.txt` (ou `cookies.txt` como fallback) dentro de `./cookies` para usar com `yt-dlp`.

## Endpoints
- `POST /download` com JSON simples `{"url": "https://..."}` retorna `{"status":"ok","file":"<nome>","download_url":"/file/<nome>"}`.
- `GET /file/{filename}` baixa o arquivo recém-baixado de `./downloads`.

## Notas de arquitetura
- `server.py` centraliza a lógica:
  - Identificação de tipo da URL e seleção de cookies.
  - `yt-dlp` com `--concurrent-fragments` e preset de formatos para baixar mais rápido e já preferir MP4.
  - Pós-processamento via `ffmpeg -c copy` para garantir saída `.mp4` mesmo quando a origem não é MP4.
  - Galeria de stories via `gallery-dl`.
- `Dockerfile` usa `python:3.11-slim`, instala só o necessário e instala dependências a partir de `requirements.txt`.
- `.dockerignore` evita que `downloads/` vire contexto de build.

## Desenvolvimento local sem Docker
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -r requirements.txt`
- `uvicorn server:app --reload --port 8080`
