# laed-audiobook

Slim CLI that turns documents or clipboard text into a stitched audiobook MP3 via **llm-gateway** (`tts/kokoro` + a chat model).

## Setup

```bash
cd laed-audiobook
/opt/homebrew/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # set LLM_GATEWAY_KEY (+ CADDY_* for public HTTPS)
```

Requires `ffmpeg` on PATH for clean stitching (`brew install ffmpeg`).

Do not inherit `LLM_GATEWAY_URL=http://litellm:4000/v1` from a sourced LAED `.env` on your Mac. That hostname only resolves inside Docker.

### Reach the gateway from a Mac

1. **Public HTTPS** (preferred day-to-day): `LLM_GATEWAY_URL=https://litellm.laed.eu/v1` plus `CADDY_USER` / `CADDY_PASS` (Caddy basicauth) and a budgeted `LLM_GATEWAY_KEY`.
2. **SSH tunnel** (debug without Caddy):

```bash
LIP=$(ssh scw-base "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' llm-gateway-litellm-1")
ssh -f -N -L 14000:${LIP}:4000 scw-base
export LLM_GATEWAY_URL=http://127.0.0.1:14000/v1
```

## Usage

```bash
audiobook clipboard --mode review
audiobook file ~/Downloads/brief.pdf --mode narrative
audiobook text "Hello from Kokoro." --raw --out ~/Desktop/hello.mp3
```

Modes: `review` (short brief), `balanced` (structured summary), `narrative` (near-full read).  
`--raw` skips the chat rewrite and speaks the extracted text. Output defaults to `~/Desktop`.

## Verify gateway TTS

```bash
./scripts/verify_gateway_tts.sh
```
