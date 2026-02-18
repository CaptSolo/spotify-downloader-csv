"""Playlist module for retrieving playlist data from Spotify.

Patch (Feb 2026 Spotify Web API changes):
- Spotify introduced a new /playlists/{id}/items endpoint and changed item shapes.
- Older responses used `items[*].track`; newer ones may use `items[*].item` (and sometimes nested).

This version is backward-compatible with both shapes.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from spotdl.types.song import Song, SongList
from spotdl.utils.spotify import SpotifyClient

__all__ = ["Playlist", "PlaylistError"]

logger = logging.getLogger(__name__)


class PlaylistError(Exception):
    """Base class for all exceptions related to playlists."""


def _extract_track_meta(entry: Any) -> Optional[Dict[str, Any]]:
    """Extract a Spotify Track object from a playlist item.

    Supports both legacy and Feb-2026 shapes:
    - legacy: {"track": {...}}
    - new:    {"item":  {...}}  (and occasionally nested {"item": {"item": {...}}})

    Returns the track dict, or None.
    """

    if not isinstance(entry, dict):
        return None

    # Legacy shape
    track = entry.get("track")
    if isinstance(track, dict):
        return track

    # New shape
    item = entry.get("item")
    if isinstance(item, dict):
        # Sometimes an extra nesting appears (defensive)
        if isinstance(item.get("item"), dict):
            item = item["item"]

        # Some APIs may wrap episodes/tracks the same way; we only want tracks
        if item.get("type") == "track" or ("album" in item and "artists" in item):
            return item

    return None


@dataclass(frozen=True)
class Playlist(SongList):
    """Playlist class for retrieving playlist data from Spotify."""

    description: str
    author_url: str
    author_name: str
    cover_url: str

    @staticmethod
    def get_metadata(url: str) -> Tuple[Dict[str, Any], List[Song]]:
        """Get metadata for a playlist."""

        spotify_client = SpotifyClient()

        playlist = spotify_client.playlist(url)
        if playlist is None:
            raise PlaylistError("Invalid playlist URL.")

        metadata = {
            "name": playlist.get("name"),
            "url": url,
            "description": playlist.get("description"),
            "author_url": (playlist.get("external_urls") or {}).get("spotify", ""),
            "author_name": ((playlist.get("owner") or {}).get("display_name")) or "",
            "cover_url": (
                max(
                    playlist.get("images") or [],
                    key=lambda i: (
                        0
                        if (i.get("width") is None or i.get("height") is None)
                        else i.get("width") * i.get("height")
                    ),
                    default={},
                ).get("url", "")
            ),
        }

        playlist_response = spotify_client.playlist_items(url)
        if playlist_response is None:
            raise PlaylistError(f"Wrong playlist id: {url}")

        # Collect all entries from paging
        entries = list(playlist_response.get("items") or [])
        while playlist_response.get("next"):
            playlist_response = spotify_client.next(playlist_response)
            if playlist_response is None:
                break
            entries.extend(list(playlist_response.get("items") or []))

        songs: List[Song] = []
        list_pos = 0

        for entry in entries:
            track_meta = _extract_track_meta(entry)
            if not track_meta:
                continue

            # Skip local tracks and unsupported types
            if track_meta.get("is_local") or track_meta.get("type") != "track":
                logger.warning(
                    "Skipping track: %s local tracks and %s are not supported",
                    track_meta.get("id"),
                    track_meta.get("type"),
                )
                continue

            track_id = track_meta.get("id")
            if track_id is None or track_meta.get("duration_ms") in (None, 0):
                continue

            album_meta = track_meta.get("album") or {}
            release_date = album_meta.get("release_date")
            artists = [a.get("name") for a in (track_meta.get("artists") or []) if a.get("name")]
            if not artists:
                continue

            # increment playlist position only for actual downloadable tracks
            list_pos += 1

            song = Song.from_missing_data(
                name=track_meta.get("name"),
                artists=artists,
                artist=artists[0],
                album_id=album_meta.get("id"),
                album_name=album_meta.get("name"),
                album_artist=(
                    (album_meta.get("artists") or [{}])[0].get("name")
                    if (album_meta.get("artists") or [])
                    else None
                ),
                album_type=album_meta.get("album_type"),
                disc_number=track_meta.get("disc_number"),
                duration=int((track_meta.get("duration_ms") or 0) / 1000),
                year=(release_date[:4] if isinstance(release_date, str) and len(release_date) >= 4 else None),
                date=release_date,
                track_number=track_meta.get("track_number"),
                tracks_count=album_meta.get("total_tracks"),
                song_id=track_id,
                explicit=track_meta.get("explicit"),
                url=(track_meta.get("external_urls") or {}).get("spotify"),
                # Feb 2026: external_ids/isrc may be missing
                isrc=(track_meta.get("external_ids") or {}).get("isrc"),
                cover_url=(
                    max(album_meta.get("images") or [], key=lambda i: (i.get("width", 0) * i.get("height", 0)), default={}).get("url")
                    if (album_meta.get("images") is not None)
                    else None
                ),
                list_position=list_pos,
            )

            songs.append(song)

        return metadata, songs
