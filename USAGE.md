# Usage Guide

This is a modified version of spotDL that uses CSV playlist files (e.g. exported from [Chosic](https://www.chosic.com/)) instead of the Spotify API. Songs are matched on YouTube Music using ISRC codes from the CSV, and YouTube video thumbnails are used as album art.

## Prerequisites

Installation commands in this guide are written for macOS (using `brew install`). For other operating systems, use the relevant install commands for installing prerequisite software.

- **Python 3.13+**
- **FFmpeg** -- install via `brew install ffmpeg` or run `spotdl --download-ffmpeg`
- **Deno** (JavaScript runtime, required by yt-dlp) -- install via `brew install deno`
- **YouTube cookies file** -- required to download from YouTube Music (see below)

## Installation

```bash
uv sync
```

## Exporting a Spotify Playlist as CSV

1. Go to [Chosic Spotify Playlist Analyzer](https://www.chosic.com/spotify-playlist-analyzer/)
2. Paste your Spotify playlist URL and click Analyze
3. Click the **Export** button and choose **CSV**
4. Save the file (e.g., `playlist.csv`)

The CSV must contain these columns: `Song`, `Artist`, `Duration`, `Spotify Track Id`, `ISRC`. Optional columns: `Album`, `Album Date`, `Genres`, `Popularity`, `#`.

## Getting YouTube Cookies

yt-dlp needs a cookies file to download from YouTube Music. Export cookies from your browser using an extension like [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc):

1. Log in to [YouTube Music](https://music.youtube.com/) in your browser
2. Use the extension to export cookies for `youtube.com`
3. Save as `cookies.txt` in the project directory

**Note:** Cookies expire periodically. If downloads fail with authentication errors, re-export fresh cookies.

## Downloading Songs

Basic download from a CSV file:

```bash
uv run spotdl download playlist.csv --cookie-file cookies.txt
```

### Common Options

```bash
# Choose output format (default: mp3)
uv run spotdl download playlist.csv --cookie-file cookies.txt --format opus

# Custom output path and filename template
uv run spotdl download playlist.csv --cookie-file cookies.txt \
    --output "output/{list-name}/{list-position} - {artist} - {title}.{output-ext}"

# Set bitrate (default: 128k)
uv run spotdl download playlist.csv --cookie-file cookies.txt --bitrate 320k

# Use original bitrate without re-encoding
uv run spotdl download playlist.csv --cookie-file cookies.txt --bitrate disable

# Use playlist numbering (track numbers from playlist position)
uv run spotdl download playlist.csv --cookie-file cookies.txt --playlist-numbering

# Multiple threads for faster downloads
uv run spotdl download playlist.csv --cookie-file cookies.txt --threads 4

# Add delay between downloads to avoid rate limiting (seconds)
uv run spotdl download playlist.csv --cookie-file cookies.txt --delay 2.5
```

### Full Example

```bash
uv run spotdl download playlist.csv \
    --cookie-file cookies.txt \
    --format opus \
    --bitrate disable \
    --threads 4 \
    --delay 1.0 \
    --output "output/{artist} - {title}.{output-ext}"
```

## Other Operations

### Save song metadata to a file (for later use)

```bash
uv run spotdl save playlist.csv --save-file songs.spotdl
```

### Download from a previously saved file

```bash
uv run spotdl download songs.spotdl --cookie-file cookies.txt
```

### Sync (download new songs, remove deleted ones)

```bash
uv run spotdl sync songs.spotdl --cookie-file cookies.txt
```

## Output Filename Variables

Use these in the `--output` template:

| Variable | Description |
|---|---|
| `{title}` | Song title |
| `{artist}` | Primary artist |
| `{artists}` | All artists |
| `{album}` | Album name |
| `{album-artist}` | Album artist |
| `{genre}` | Genre |
| `{disc-number}` | Disc number |
| `{disc-count}` | Total discs |
| `{duration}` | Duration in seconds |
| `{year}` | Release year |
| `{track-number}` | Track number |
| `{tracks-count}` | Total tracks |
| `{isrc}` | ISRC code |
| `{list-name}` | Playlist/list name |
| `{list-position}` | Position in playlist |
| `{output-ext}` | File extension |

## Troubleshooting

### "Signature solving failed" / "JS runtimes: none"

Install deno: `brew install deno`. The `yt-dlp-ejs` package (included as a dependency) uses deno to solve YouTube's JavaScript challenges.

### "YT-DLP download error"

Usually means expired cookies. Re-export fresh cookies from your browser.

### "Requested format is not available"

Update yt-dlp: `uv lock --upgrade-package yt-dlp && uv sync`
