# Architecture

Mac CLI → llm-gateway → Kokoro (Speaches) on the CPU host.

1. Extract text from PDF / Markdown / HTML / plain text / clipboard.
2. Rewrite with a chat model into a spoken script (`review` | `balanced` | `narrative`).
   Long sources are split into non-overlapping sections and rewritten sequentially,
   each part receiving the previous script ending as continuity context (not spoken).
   Joined scripts pass through seam dedupe to drop near-repeated sentences.
3. Chunk at sentence boundaries (~220 words). No spoken bridge echoes between chunks.
4. Call `POST /v1/audio/speech` with model `tts/kokoro` and optional pace speed.
5. Stitch MP3 segments with ffmpeg (short crossfade) and write to Desktop.

Gateway contract matches LAED consumers: `LLM_GATEWAY_URL` + budgeted `LLM_GATEWAY_KEY`.
