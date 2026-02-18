"""
Artist module. Stubbed - use CSV files instead.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from spotdl.types.album import Album
from spotdl.types.song import Song, SongList

__all__ = ["Artist", "ArtistError"]


class ArtistError(Exception):
    """
    Base class for all exceptions related to artists.
    """


@dataclass(frozen=True)
class Artist(SongList):
    """
    Artist class.
    Contains all the information about an artist.
    Frozen to prevent accidental modification.
    """

    genres: List[str]
    albums: List[Album]

    @staticmethod
    def get_metadata(url: str) -> Tuple[Dict[str, Any], List[Song]]:
        """
        Get metadata for artist.

        ### Arguments
        - url: The URL of the artist.

        ### Returns
        - Dict with metadata for artist.
        """

        raise NotImplementedError("Use CSV file instead")
