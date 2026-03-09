"""
Module for functions related to downloading songs.
"""

import logging
import re
from typing import Dict, Iterable, Optional

import requests

from spotdl.types.song import Song
from spotdl.utils.config import GlobalConfig

__all__ = [
    "check_ytmusic_connection",
    "find_musicbrainz_cover_url",
    "pick_thumbnail_url",
]

logger = logging.getLogger(__name__)

MUSICBRAINZ_API = "https://musicbrainz.org/ws/2/isrc/{isrc}"
COVER_ART_ARCHIVE_API = "https://coverartarchive.org/release/{release_id}"
USER_AGENT = "spotdl-csv/4.4.3 (https://github.com/CaptSolo/spotify-downloader-csv)"


def _normalize_text(value: Optional[str]) -> str:
    """
    Normalize text for loose equality checks.
    """

    if not value:
        return ""

    return re.sub(r"[^a-z0-9]+", "", value.lower())


def pick_thumbnail_url(thumbnails: Optional[Iterable[Dict]]) -> Optional[str]:
    """
    Pick the most suitable cover-art thumbnail, favoring square and larger images.

    ### Arguments
    - thumbnails: Iterable of thumbnail dictionaries.

    ### Returns
    - The selected thumbnail URL if available.
    """

    best_url = None
    best_key = None

    for thumb in thumbnails or []:
        url = thumb.get("url")
        if not url:
            continue

        width = thumb.get("width") or 0
        height = thumb.get("height") or 0
        max_side = max(width, height)
        squareness = (
            1 - abs(width - height) / max_side if max_side and width and height else 0
        )
        area = width * height
        preference = thumb.get("preference", 0)
        is_non_webp = ".webp" not in url

        key = (
            is_non_webp,
            squareness,
            area,
            preference,
        )

        if best_key is None or key > best_key:
            best_key = key
            best_url = url

    return best_url


def _get_cover_art_archive_url(release_id: str) -> Optional[str]:
    """
    Resolve a Cover Art Archive image URL for a MusicBrainz release ID.
    """

    try:
        response = requests.get(
            COVER_ART_ARCHIVE_API.format(release_id=release_id),
            timeout=10,
            proxies=GlobalConfig.get_parameter("proxies"),
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except Exception:
        return None

    payload = response.json()
    for image in payload.get("images", []):
        if not image.get("front"):
            continue

        thumbnails = image.get("thumbnails", {})
        return (
            thumbnails.get("500")
            or thumbnails.get("large")
            or thumbnails.get("250")
            or image.get("image")
        )

    return None


def find_musicbrainz_cover_url(song: Song) -> Optional[str]:
    """
    Resolve a square cover image using MusicBrainz and the Cover Art Archive.

    ### Arguments
    - song: Song object.

    ### Returns
    - A cover URL if one could be resolved.
    """

    if not song.isrc:
        return None

    try:
        response = requests.get(
            MUSICBRAINZ_API.format(isrc=song.isrc),
            params={"fmt": "json", "inc": "recordings+releases"},
            timeout=10,
            proxies=GlobalConfig.get_parameter("proxies"),
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        logger.debug("MusicBrainz lookup failed for %s: %s", song.display_name, exc)
        return None

    normalized_album = _normalize_text(song.album_name)
    release_candidates = []
    seen_release_ids = set()

    for recording in payload.get("recordings", []):
        for release in recording.get("releases", []):
            release_id = release.get("id")
            if not release_id or release_id in seen_release_ids:
                continue

            seen_release_ids.add(release_id)

            score = 0
            release_title = _normalize_text(release.get("title"))
            if normalized_album and release_title == normalized_album:
                score += 50
            elif normalized_album and normalized_album in release_title:
                score += 20

            if release.get("status") == "Official":
                score += 10

            release_date = release.get("date", "")
            if song.year and release_date.startswith(str(song.year)):
                score += 5

            release_candidates.append((score, release_id))

    for _score, release_id in sorted(release_candidates, reverse=True):
        cover_url = _get_cover_art_archive_url(release_id)
        if cover_url:
            return cover_url

    return None


def check_ytmusic_connection() -> bool:
    """
    Check if we can connect to YouTube Music API

    ### Returns
    - `True` if we can connect to YouTube Music API
    - `False` if we can't connect to YouTube Music API
    """

    from spotdl.providers.audio import YouTubeMusic

    # Check if we are getting results from YouTube Music
    ytm = YouTubeMusic()
    test_results = ytm.get_results("a")
    if len(test_results) == 0:
        return False

    return True
