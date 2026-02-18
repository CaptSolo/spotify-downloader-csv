"""
Album module. Stubbed - use CSV files instead.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from spotdl.types.song import Song, SongList

__all__ = ["Album", "AlbumError"]


class AlbumError(Exception):
    """
    Base class for all exceptions related to albums.
    """


@dataclass(frozen=True)
class Album(SongList):
    """
    Album class for retrieving album data from Spotify.
    """

    artist: Dict[str, Any]

    @staticmethod
    def get_metadata(url: str) -> Tuple[Dict[str, Any], List[Song]]:
        """
        Get metadata for album.

        ### Arguments
        - url: The URL of the album.

        ### Returns
        - A dictionary with metadata.
        """

        raise NotImplementedError("Use CSV file instead")
