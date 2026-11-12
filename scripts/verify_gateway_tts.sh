#!/usr/bin/env bash
# Smoke: gateway lists tts/kokoro and returns a tiny MP3.
set -euo pipefail

: "${LLM_GATEWAY_URL:?Set LLM_GATEWAY_URL (e.g. https://litellm.laed.eu/v1)}"
: "${LLM_GATEWAY_KEY:?Set LLM_GATEWAY_KEY}"

BASE="${LLM_GATEWAY_URL%/}"
OUT="${TMPDIR:-/tmp}/kokoro-verify.mp3"

echo "==> GET ${BASE}/models"
curl -sS -H "Authorization: Bearer ${LLM_GATEWAY_KEY}" "${BASE}/models" \
  | python3 -c 'import json,sys; ids=[m["id"] for m in json.load(sys.stdin).get("data",[])];
assert "tts/kokoro" in ids, ids[:20]; print("tts/kokoro ok")'

echo "==> POST ${BASE}/audio/speech"
curl -sS -H "Authorization: Bearer ${LLM_GATEWAY_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"tts/kokoro","input":"Gateway verify.","voice":"af_heart"}' \
  --output "${OUT}"

python3 - <<PY
from pathlib import Path
p = Path("${OUT}")
assert p.stat().st_size > 500, p.stat().st_size
print(f"wrote {p} ({p.stat().st_size} bytes)")
PY
