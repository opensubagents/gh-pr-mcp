---
name: yt-transcript-cherny-ai-ascent
description: Fetch the transcript / captions of Boris Cherny's AI Ascent 2026 talk on Claude Code (YouTube video SlGRN8jh2RI, "Why Coding Is Solved, and What Comes Next" with Sequoia partner Lauren Reeder). Use this skill whenever the user asks for the transcript, captions, subtitles, or text version of this specific video, links to https://youtu.be/SlGRN8jh2RI or https://www.youtube.com/watch?v=SlGRN8jh2RI, asks "what did Boris Cherny say at AI Ascent", or wants quotes / specific claims sourced from this talk. Do NOT use this skill for other YouTube videos — it is hardcoded to this single video.
---

# YouTube transcript: Boris Cherny — AI Ascent 2026

This skill fetches the captions for one specific video and saves them to a local file. It is intentionally narrow: video ID `SlGRN8jh2RI`.

## What it does

Runs `scripts/fetch_transcript.py`, which tries three fetch methods in order and falls back to manual instructions if all fail:

1. **`youtube-transcript-api`** — cleanest output, hits YouTube's timedtext endpoint via the library.
2. **`yt-dlp`** — downloads the auto-generated `.vtt` and cleans it to plain text.
3. **Watch-page scrape** — fetches the watch page, extracts the `captionTracks` JSON, then fetches the timedtext URL directly.

The script writes to `/home/claude/transcripts/cherny_ai_ascent.txt` (override with `OUT_DIR=...`). Each line is timestamped `[MM:SS] text` so the output is searchable by chapter.

## How to use it

1. Run the script:
   ```bash
   python3 /path/to/this-skill/scripts/fetch_transcript.py
   ```
   The script prints a single JSON status line on stdout. Diagnostics go to stderr.

2. Read the resulting file to answer the user's question. Do **not** paste the full transcript into the chat — it's the speaker's copyrighted content. Instead:
   - Summarize sections the user asked about.
   - Quote sparingly (short verbatim phrases only) when the user asks for exact wording, and cite the timestamp.
   - Offer the file to the user via `present_files` so they can read or process the full text themselves.

3. If the JSON status is `"fallback"`, all automated methods were blocked (almost always cloud-IP bot detection). The output file then contains manual instructions — relay those to the user; don't pretend the transcript was retrieved.

## Output contract

stdout (one line of JSON):
```json
{"status": "ok",       "method": "youtube-transcript-api", "path": "/home/claude/transcripts/cherny_ai_ascent.txt"}
{"status": "fallback", "method": "manual-instructions",    "path": "/home/claude/transcripts/cherny_ai_ascent.txt"}
```

The first line of the output file always identifies which method produced it, so you can tell at a glance whether you're looking at real captions or fallback instructions.

## Known limitations

- **Cloud-IP blocking**: YouTube blanket-blocks most cloud-provider IPs. Running this from a typical sandbox / serverless environment usually hits the fallback path. Running from a residential IP (e.g. Claude Code on a laptop) generally works.
- **No translation**: The script prefers manual English captions and falls back to auto-generated English. It does not translate other languages.
- **Single video only**: The video ID is hardcoded. For other videos, write a different skill or generalize this one.

## Dependencies

- `python3` (stdlib only for method 3)
- `youtube-transcript-api` (optional, enables method 1): `pip install youtube-transcript-api`
- `yt-dlp` (optional, enables method 2): `pip install yt-dlp`

The script gracefully skips any method whose dependency is missing.
