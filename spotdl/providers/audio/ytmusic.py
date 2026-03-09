"""
YTMusic module for downloading and searching songs.
"""

from typing import Any, Dict, List, Optional

from ytmusicapi import YTMusic

from spotdl.providers.audio.base import ISRC_REGEX, AudioProvider
from spotdl.types.result import Result
from spotdl.types.song import Song
from spotdl.utils.downloader import pick_thumbnail_url
from spotdl.utils.formatter import create_song_title, parse_duration
from spotdl.utils.matching import order_results

__all__ = ["YouTubeMusic"]


class YouTubeMusic(AudioProvider):
    """
    YouTube Music audio provider class
    """

    SUPPORTS_ISRC = True
    GET_RESULTS_OPTS: List[Dict[str, Any]] = [
        {"filter": "songs", "ignore_spelling": True, "limit": 50},
        {"filter": "videos", "ignore_spelling": True, "limit": 50},
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the YouTube Music API

        ### Arguments
        - args: Arguments passed to the `AudioProvider` class.
        - kwargs: Keyword arguments passed to the `AudioProvider` class.
        """

        super().__init__(*args, **kwargs)

        self.client = YTMusic(language="de")

    def get_results(self, search_term: str, **kwargs) -> List[Result]:
        """
        Get results from YouTube Music API and simplify them

        ### Arguments
        - search_term: The search term to search for.
        - kwargs: other keyword arguments passed to the `YTMusic.search` method.

        ### Returns
        - A list of simplified results (dicts)
        """

        is_isrc_result = ISRC_REGEX.search(search_term) is not None
        # if is_isrc_result:
        #     print("FORCEFULLY SETTING FILTER TO SONGS")
        #     kwargs["filter"] = "songs"

        search_results = self.client.search(search_term, **kwargs)

        # Simplify results
        results = []
        for result in search_results:
            if (
                result is None
                or result.get("videoId") is None
                or result.get("artists") in [[], None]
            ):
                continue

            results.append(
                Result(
                    source=self.name,
                    url=(
                        f'https://{"music" if result["resultType"] == "song" else "www"}'
                        f".youtube.com/watch?v={result['videoId']}"
                    ),
                    verified=result.get("resultType") == "song",
                    name=result["title"],
                    result_id=result["videoId"],
                    author=result["artists"][0]["name"],
                    artists=tuple(map(lambda a: a["name"], result["artists"])),
                    duration=parse_duration(result.get("duration")),
                    isrc_search=is_isrc_result,
                    search_query=search_term,
                    explicit=result.get("isExplicit"),
                    album=(
                        result.get("album", {}).get("name")
                        if result.get("album")
                        else None
                    ),
                    album_id=(
                        result.get("album", {}).get("id")
                        if result.get("album")
                        else None
                    ),
                )
            )

        return results

    def get_album_cover_url(self, album_id: str) -> Optional[str]:
        """
        Resolve cover art for a YouTube Music album.

        ### Arguments
        - album_id: Album browse ID.

        ### Returns
        - A square album-art URL if available.
        """

        if not album_id:
            return None

        album = self.client.get_album(album_id)

        return pick_thumbnail_url(album.get("thumbnails"))

    def _find_cover_album_id(self, song: Song) -> Optional[str]:
        """
        Search YouTube Music song results specifically for album art resolution.
        """

        search_terms = []
        if song.isrc:
            search_terms.append(song.isrc)

        title_query = create_song_title(song.name, song.artists).lower()
        if title_query not in search_terms:
            search_terms.append(title_query)

        for search_term in search_terms:
            song_results = [
                result
                for result in self.get_results(
                    search_term,
                    filter="songs",
                    ignore_spelling=True,
                    limit=10,
                )
                if result.album_id
            ]
            if not song_results:
                continue

            if len(song_results) == 1:
                return song_results[0].album_id

            ordered_results = order_results(song_results, song, self.search_query)
            if ordered_results:
                best_result, _score = self.get_best_result(ordered_results)
                if best_result.album_id:
                    return best_result.album_id

            return song_results[0].album_id

        return None

    def get_cover_url(
        self, song: Song, result: Optional[Result] = None
    ) -> Optional[str]:
        """
        Resolve cover art for a song via its YouTube Music album metadata.

        ### Arguments
        - song: Song object.
        - result: Optional matched search result to reuse.

        ### Returns
        - A square album-art URL if available.
        """

        tried_album_ids = set()
        if result and result.album_id:
            tried_album_ids.add(result.album_id)
            cover_url = self.get_album_cover_url(result.album_id)
            if cover_url:
                return cover_url

        searched_album_id = self._find_cover_album_id(song)
        if searched_album_id and searched_album_id not in tried_album_ids:
            return self.get_album_cover_url(searched_album_id)

        return None
