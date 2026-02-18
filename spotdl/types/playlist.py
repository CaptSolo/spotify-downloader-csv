"""
Playlist module. Stubbed - use CSV files instead.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from spotdl.types.song import Song, SongList

__all__ = ["Playlist", "PlaylistError"]


class PlaylistError(Exception):
    """Base class for all exceptions related to playlists."""


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

        raise NotImplementedError("Use CSV file instead")
