"""
Stub module for the removed Spotify API integration.
The Spotify API has been replaced with CSV-based input.
"""

__all__ = [
    "SpotifyError",
    "SpotifyClient",
    "save_spotify_cache",
]


class SpotifyError(Exception):
    """
    Base class for all exceptions related to SpotifyClient.
    """


class SpotifyClient:
    """
    Stub for the removed SpotifyClient.
    Raises RuntimeError if anyone tries to initialize it.
    """

    @classmethod
    def init(cls, **kwargs):
        """
        Raises RuntimeError since Spotify API has been removed.
        """

        raise RuntimeError("Spotify API has been removed. Use CSV files instead.")

    def __init__(self):
        raise RuntimeError("Spotify API has been removed. Use CSV files instead.")


def save_spotify_cache(cache=None):  # pylint: disable=unused-argument
    """
    No-op stub for backward compatibility.
    """
