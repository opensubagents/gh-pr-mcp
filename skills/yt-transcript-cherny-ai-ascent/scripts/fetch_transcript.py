#!/usr/bin/env python3
"""
Fetch the transcript of Boris Cherny's AI Ascent 2026 talk on Claude Code.
Video: https://www.youtube.com/watch?v=SlGRN8jh2RI

Tries three methods in order. Writes results to OUT_PATH and prints a JSON
status line so the calling Claude knows what happened.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

VIDEO_ID = "SlGRN8jh2RI"
VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"
OUT_DIR = Path(os.environ.get("OUT_DIR", "/home/claude/transcripts"))
OUT_PATH = OUT_DIR / "cherny_ai_ascent.txt"


def log(msg: str) -> None:
    print(f"[fetch_transcript] {msg}", file=sys.stderr)


def write_output(text: str, source: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header = (
        f"Transcript: Boris Cherny — Why Coding Is Solved, and What Comes Next\n"
        f"Source: {VIDEO_URL}\n"
        f"Fetched via: {source}\n"
        f"{'=' * 70}\n\n"
    )
    OUT_PATH.write_text(header + text, encoding="utf-8")


def try_youtube_transcript_api() -> bool:
    """Method 1: youtube-transcript-api (cleanest output)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        log("youtube-transcript-api not installed; skipping")
        return False
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(VIDEO_ID, languages=["en", "en-US", "en-GB"])
        lines = []
        for snippet in fetched:
            mm = int(snippet.start) // 60
            ss = int(snippet.start) % 60
            lines.append(f"[{mm:02d}:{ss:02d}] {snippet.text}")
        write_output("\n".join(lines), "youtube-transcript-api")
        log(f"OK via youtube-transcript-api ({len(lines)} segments)")
        return True
    except Exception as e:
        log(f"youtube-transcript-api failed: {type(e).__name__}: {str(e)[:200]}")
        return False


def try_yt_dlp() -> bool:
    """Method 2: yt-dlp writes auto-subs as VTT, we convert to plain text."""
    if shutil.which("yt-dlp") is None:
        log("yt-dlp not on PATH; skipping")
        return False
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_template = str(OUT_DIR / f"{VIDEO_ID}.%(ext)s")
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", "en.*",
        "--sub-format", "vtt",
        "--no-check-certificates",
        "-o", out_template,
        VIDEO_URL,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            log(f"yt-dlp exit {proc.returncode}: {proc.stderr.strip()[-300:]}")
            return False
    except subprocess.TimeoutExpired:
        log("yt-dlp timed out")
        return False

    vtt_files = list(OUT_DIR.glob(f"{VIDEO_ID}*.vtt"))
    if not vtt_files:
        log("yt-dlp ran but produced no .vtt file")
        return False

    text = vtt_to_plain(vtt_files[0].read_text(encoding="utf-8"))
    write_output(text, f"yt-dlp ({vtt_files[0].name})")
    log(f"OK via yt-dlp ({len(text)} chars)")
    return True


def vtt_to_plain(vtt: str) -> str:
    """Strip VTT headers, timestamps, and dedupe rolling-caption repeats."""
    out_lines = []
    last = None
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line:
            ts = line.split(" ")[0]
            mm_ss = ts.split(".")[0]
            parts = mm_ss.split(":")
            if len(parts) == 3:
                mm_ss = f"{int(parts[0]) * 60 + int(parts[1]):02d}:{parts[2]}"
            out_lines.append(f"\n[{mm_ss}]")
            continue
        # Strip inline VTT tags like <c> and timestamp tags
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean and clean != last:
            out_lines.append(clean)
            last = clean
    return "\n".join(out_lines)


def try_watch_page() -> bool:
    """Method 3: scrape the watch page for the timedtext URL, fetch the XML."""
    req = urllib.request.Request(
        VIDEO_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"watch page fetch failed: {type(e).__name__}: {str(e)[:200]}")
        return False

    m = re.search(r'"captionTracks":(\[.*?\])', html)
    if not m:
        log("no captionTracks in watch page")
        return False
    try:
        tracks = json.loads(m.group(1))
    except Exception as e:
        log(f"captionTracks parse failed: {e}")
        return False

    # Prefer manual English, fall back to ASR
    track = next((t for t in tracks if t.get("languageCode", "").startswith("en") and t.get("kind") != "asr"), None)
    if track is None:
        track = next((t for t in tracks if t.get("languageCode", "").startswith("en")), None)
    if track is None:
        log("no English caption track found")
        return False

    base_url = track["baseUrl"].replace("\\u0026", "&")
    if "fmt=" not in base_url:
        base_url += "&fmt=json3"

    try:
        with urllib.request.urlopen(base_url, timeout=20) as resp:
            data = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"timedtext fetch failed: {type(e).__name__}: {str(e)[:200]}")
        return False

    lines = []
    try:
        payload = json.loads(data)
        for ev in payload.get("events", []):
            if "segs" not in ev:
                continue
            start_ms = ev.get("tStartMs", 0)
            mm = start_ms // 60000
            ss = (start_ms // 1000) % 60
            text = "".join(s.get("utf8", "") for s in ev["segs"]).replace("\n", " ").strip()
            if text:
                lines.append(f"[{mm:02d}:{ss:02d}] {text}")
    except Exception:
        # Plain XML fallback
        for m2 in re.finditer(r'<text start="([\d.]+)"[^>]*>(.*?)</text>', data, re.DOTALL):
            start = float(m2.group(1))
            mm = int(start) // 60
            ss = int(start) % 60
            text = re.sub(r"<[^>]+>", "", m2.group(2)).strip()
            text = (
                text.replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&#39;", "'")
                    .replace("&quot;", '"')
            )
            if text:
                lines.append(f"[{mm:02d}:{ss:02d}] {text}")

    if not lines:
        log("timedtext returned no captions")
        return False

    write_output("\n".join(lines), "watch-page + timedtext API")
    log(f"OK via watch-page scrape ({len(lines)} segments)")
    return True


def write_manual_instructions() -> None:
    """All automated paths failed — leave clear directions for a human."""
    text = (
        "Automated fetch could not reach YouTube from this environment.\n"
        "This is almost always because the runtime IP is blocked by YouTube's\n"
        "bot protection (common on cloud-provider IPs).\n\n"
        "Two reliable manual options:\n\n"
        f"1. YouTube's own transcript panel\n"
        f"   - Open {VIDEO_URL}\n"
        f"   - Click the '...' menu under the video → 'Show transcript'\n"
        f"   - Select all text in the transcript pane and copy it\n\n"
        "2. tactiq.io (or similar)\n"
        f"   - Go to https://tactiq.io/tools/youtube-transcript\n"
        f"   - Paste {VIDEO_URL} and download the plain text\n\n"
        "3. yt-dlp on a non-cloud IP (e.g. your laptop):\n"
        f"   yt-dlp --write-auto-sub --skip-download --sub-lang en \\\n"
        f"     -o '%(id)s.%(ext)s' {VIDEO_URL}\n"
        "   This produces a .vtt file that can be cleaned to plain text.\n"
    )
    write_output(text, "manual-fallback (all automated methods blocked)")
    log("Wrote manual-fallback instructions")


def main() -> int:
    methods = [
        ("youtube-transcript-api", try_youtube_transcript_api),
        ("yt-dlp",                 try_yt_dlp),
        ("watch-page scrape",      try_watch_page),
    ]
    for name, fn in methods:
        log(f"trying: {name}")
        if fn():
            print(json.dumps({"status": "ok", "method": name, "path": str(OUT_PATH)}))
            return 0

    write_manual_instructions()
    print(json.dumps({"status": "fallback", "method": "manual-instructions", "path": str(OUT_PATH)}))
    return 2


if __name__ == "__main__":
    sys.exit(main())
