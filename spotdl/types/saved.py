"""
Saved module. Stubbed - use CSV files instead.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from spotdl.types.song import Song, SongList

__all__ = ["Saved", "SavedError"]


class SavedError(Exception):
    """
    Base class for all exceptions related to saved tracks.
    """


@dataclass(frozen=True)
class Saved(SongList):
    """
    Saved class for handling the saved tracks from user library.
    """

    @staticmethod
    def get_metadata(url: str = "saved") -> Tuple[Dict[str, Any], List[Song]]:
        """
        Returns metadata for a saved list.

        ### Arguments
        - url: Not required.

        ### Returns
        - metadata and songs.
        """

        raise NotImplementedError("Use CSV file instead")
