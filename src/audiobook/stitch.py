from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def stitch_mp3_segments(
    segment_paths: list[Path],
    output_path: Path,
    *,
    crossfade_ms: int = 30,
) -> Path:
    if not segment_paths:
        raise ValueError("No audio segments to stitch.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if len(segment_paths) == 1:
        output_path.write_bytes(segment_paths[0].read_bytes())
        return output_path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        # Fallback: naive byte concat works poorly for MP3; still better than failing
        # when ffmpeg is absent on a minimal machine.
        with output_path.open("wb") as out:
            for path in segment_paths:
                out.write(path.read_bytes())
        return output_path

    with tempfile.TemporaryDirectory(prefix="audiobook-stitch-") as tmp:
        tmp_dir = Path(tmp)
        list_file = tmp_dir / "concat.txt"
        lines = [f"file '{path.resolve()}'" for path in segment_paths]
        list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        if crossfade_ms <= 0 or len(segment_paths) < 2:
            cmd = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                str(output_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path

        # Re-encode with short acrossfade between adjacent segments.
        fade_s = max(crossfade_ms, 1) / 1000.0
        inputs: list[str] = []
        for path in segment_paths:
            inputs.extend(["-i", str(path)])
        filter_parts: list[str] = []
        last = "[0:a]"
        for i in range(1, len(segment_paths)):
            out_label = f"[a{i}]" if i < len(segment_paths) - 1 else "[outa]"
            filter_parts.append(
                f"{last}[{i}:a]acrossfade=d={fade_s}:c1=tri:c2=tri{out_label}"
            )
            last = out_label
        filter_complex = ";".join(filter_parts)
        cmd = [
            ffmpeg,
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[outa]",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
