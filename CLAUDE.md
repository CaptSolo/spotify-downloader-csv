# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

spotDL is a Python CLI tool and library that downloads songs by finding them on YouTube Music and embedding metadata (album art, lyrics, etc.). Song metadata comes from CSV playlist files exported from Chosic (no Spotify API required). Built with Python 3.13+, uses Hatchling as build backend and `uv` as package manager.

## Common Commands

```bash
# Install dependencies
uv sync

# Run the tool (CSV file as input)
uv run spotdl download playlist.csv --cookie-file cookies.txt

# Run all tests (uses VCR cassettes by default)
uv run pytest

# Run a single test file
uv run pytest tests/test_matching.py -vvv

# Run tests with real network calls
uv run pytest --disable-vcr

# Linting (all must pass in CI)
uv run pylint --fail-under 10 --limit-inference-results 0 --disable=R0917 ./spotdl
uv run mypy --ignore-missing-imports --follow-imports silent --install-types --non-interactive ./spotdl
uv run black --check ./spotdl
uv run isort --check --diff ./spotdl

# Auto-fix formatting
uv run black ./spotdl
uv run isort ./spotdl

# Build standalone executable
uv run python ./scripts/build.py
```

FFmpeg and Deno are required at runtime. Install FFmpeg via `brew install ffmpeg` or run `spotdl --download-ffmpeg`. Install Deno via `brew install deno` (needed by yt-dlp for YouTube signature solving).

## Architecture

**Entry point:** `spotdl/console/entry_point.py` → `console_entry_point()` (CLI via `spotdl` command or `python -m spotdl`)

**Public API:** The `Spotdl` class in `spotdl/__init__.py` is the programmatic interface.

**Key packages:**

- `spotdl/console/` — CLI operation handlers: `download`, `save`, `sync`, `meta`, `url`, `web`
- `spotdl/download/downloader.py` — Core `Downloader` class orchestrating search → download → convert → embed metadata. Injects YouTube thumbnails as cover art when `cover_url` is None.
- `spotdl/providers/audio/` — Audio source backends (YouTube, YouTubeMusic, SoundCloud, BandCamp, Piped)
- `spotdl/providers/lyrics/` — Lyrics source backends (Genius, AzLyrics, MusixMatch, Synced)
- `spotdl/types/` — Data models: `Song`, `Album`, `Artist`, `Playlist`, `Saved`. Album/Artist/Playlist/Saved types are stubbed (raise `NotImplementedError`).
- `spotdl/utils/` — Shared utilities (CSV parser, search/matching, metadata embedding, FFmpeg, config, formatters)
- `spotdl/utils/csv.py` — Parses Chosic-format CSV files into `Song` objects
- `spotdl/utils/spotify.py` — Stub module (Spotify API removed). `SpotifyClient` raises `RuntimeError`.

**Data flow:** CLI args → `parse_query()` routes `.csv` files to `parse_csv()` which creates `Song` objects → `Downloader` searches audio providers for YouTube matches (using ISRC codes) → downloads via `yt-dlp` (with optional `--delay` between requests) → converts with FFmpeg → embeds metadata via `utils/metadata.py`

**Web mode:** `spotdl web` starts a FastAPI/Uvicorn server with a web UI. Spotify-dependent API routes return HTTP 410.

## CSV Input Format

Songs are imported from CSV files exported by [Chosic](https://www.chosic.com/spotify-playlist-analyzer/). Required columns: `Song`, `Artist`, `Duration`, `Spotify Track Id`, `ISRC`. Optional: `Album`, `Album Date`, `Genres`, `Popularity`, `#`.

## Code Style

- **Formatter:** black, **Import sorting:** isort (profile=black)
- **Line length:** 100 characters, **Indent:** 4 spaces
- **Docstrings:** One-liner summary, then `### Args`, `### Returns`, `### Errors`, `### Notes` sections
- **Pylint** must score 10/10. Globally disabled: R0902, R0913, R0915, R0912, R0801, R0903, R0914, W0703, W0640

## Testing

- Tests use `vcrpy` to record/replay HTTP interactions (cassettes in `tests/*/cassettes/`)
- `conftest.py` patches `subprocess.Popen` (FFmpeg) and mocks download methods
- Uses `pytest-asyncio` with `asyncio_mode = "auto"`
- Some tests are excluded in CI (require live network): `test_ffmpeg.py`, `test_metadata.py`, `test_youtube.py`, `test_entry_point.py`, `test_init.py`

## Key Dependencies

- `yt-dlp` + `yt-dlp-ejs` — YouTube downloading with JS challenge solving (requires Deno runtime)
- `ytmusicapi` — YouTube Music search and matching
- `mutagen` — Audio metadata embedding
- `rapidfuzz` — Fuzzy string matching for song matching
- `fastapi` + `uvicorn` — Web UI server
