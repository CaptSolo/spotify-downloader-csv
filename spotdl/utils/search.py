"""
Module for creating Song objects by parsing a query.
Supports CSV files, .spotdl files, and YouTube URLs.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ytmusicapi import YTMusic

from spotdl.types.album import Album
from spotdl.types.song import Song, SongList
from spotdl.utils.csv import parse_csv
from spotdl.utils.metadata import get_file_metadata

__all__ = [
    "QueryError",
    "parse_query",
    "get_simple_songs",
    "reinit_song",
    "get_song_from_file_metadata",
    "gather_known_songs",
    "create_ytm_album",
    "create_ytm_playlist",
]

logger = logging.getLogger(__name__)
client = None  # pylint: disable=invalid-name


def get_ytm_client() -> YTMusic:
    """
    Lazily initialize the YTMusic client.

    ### Returns
    - the YTMusic client
    """

    global client  # pylint: disable=global-statement
    if client is None:
        client = YTMusic()

    return client


class QueryError(Exception):
    """
    Base class for all exceptions related to query.
    """


def parse_query(  # pylint: disable=unused-argument
    query: List[str],
    threads: int = 1,
    use_ytm_data: bool = False,
    playlist_numbering: bool = False,
    album_type=None,
    playlist_retain_track_cover: bool = False,
) -> List[Song]:
    """
    Parse query and return list containing song object

    ### Arguments
    - query: List of strings containing query
    - threads: Number of threads to use

    ### Returns
    - List of song objects
    """

    songs: List[Song] = get_simple_songs(
        query,
        use_ytm_data=use_ytm_data,
        playlist_numbering=playlist_numbering,
        album_type=album_type,
        playlist_retain_track_cover=playlist_retain_track_cover,
    )

    return songs


def get_simple_songs(  # pylint: disable=unused-argument
    query: List[str],
    use_ytm_data: bool = False,
    playlist_numbering: bool = False,
    albums_to_ignore=None,
    album_type=None,
    playlist_retain_track_cover: bool = False,
) -> List[Song]:
    """
    Parse query and return list containing simple song objects

    ### Arguments
    - query: List of strings containing query

    ### Returns
    - List of simple song objects
    """

    songs: List[Song] = []
    lists: List[SongList] = []
    for request in query:
        logger.info("Processing query: %s", request)

        if request.endswith(".csv"):
            songs.extend(parse_csv(request))
        elif (
            "watch?v=" in request
            or "youtu.be/" in request
            or "soundcloud.com/" in request
            or "bandcamp.com/" in request
        ):
            songs.append(Song.from_missing_data(download_url=request))
        elif "music.youtube.com/watch?v" in request:
            track_data = get_ytm_client().get_song(request.split("?v=", 1)[1])

            yt_song = Song.from_missing_data(
                name=track_data["videoDetails"]["title"],
                artist=track_data["videoDetails"]["author"],
                artists=[track_data["videoDetails"]["author"]],
                duration=int(track_data["videoDetails"]["lengthSeconds"]),
                download_url=request,
            )

            songs.append(yt_song)
        elif (
            "youtube.com/playlist?list=" in request
            or "youtube.com/browse/VLPL" in request
        ):
            request = request.replace(
                "https://www.youtube.com/", "https://music.youtube.com/"
            )
            request = request.replace(
                "https://youtube.com/", "https://music.youtube.com/"
            )

            if "?list=OLAK5uy_" in request:
                lists.append(create_ytm_album(request, fetch_songs=False))
            elif "?list=PL" in request or "browse/VLPL" in request:
                lists.append(create_ytm_playlist(request, fetch_songs=False))
        elif request.endswith(".spotdl"):
            with open(request, "r", encoding="utf-8") as save_file:
                for track in json.load(save_file):
                    # Append to songs
                    songs.append(Song.from_dict(track))
        else:
            raise QueryError(
                f"Unsupported query: {request}. "
                "Use a CSV file, .spotdl file, or YouTube URL."
            )

    for song_list in lists:
        logger.info(
            "Found %s songs in %s (%s)",
            len(song_list.urls),
            song_list.name,
            song_list.__class__.__name__,
        )

        for song in song_list.songs:
            song_data = song.json
            song_data["list_name"] = song_list.name
            song_data["list_url"] = song_list.url
            song_data["list_position"] = song.list_position
            song_data["list_length"] = song_list.length

            if playlist_numbering:
                song_data["track_number"] = song_data["list_position"]
                song_data["tracks_count"] = song_data["list_length"]
                song_data["album_name"] = song_data["list_name"]
                song_data["disc_number"] = 1
                song_data["disc_count"] = 1

            if playlist_retain_track_cover:
                song_data["track_number"] = song_data["list_position"]
                song_data["tracks_count"] = song_data["list_length"]
                song_data["album_name"] = song_data["list_name"]
                song_data["disc_number"] = 1
                song_data["disc_count"] = 1
                song_data["cover_url"] = song_data["cover_url"]

            songs.append(Song.from_dict(song_data))

    # removing songs for --ignore-albums
    original_length = len(songs)
    if albums_to_ignore:
        songs = [
            song
            for song in songs
            if all(
                keyword not in song.album_name.lower() for keyword in albums_to_ignore
            )
        ]
        logger.info("Skipped %s songs (Ignored albums)", (original_length - len(songs)))

    if album_type:
        songs = [song for song in songs if song.album_type == album_type]

        logger.info(
            "Skipped %s songs for Album Type %s",
            (original_length - len(songs)),
            album_type,
        )

    logger.debug("Found %s songs in %s lists", len(songs), len(lists))

    return songs


def reinit_song(song: Song) -> Song:
    """
    No-op: CSV songs are fully hydrated.

    ### Arguments
    - song: Song object

    ### Returns
    - The same song object
    """

    return song


def get_song_from_file_metadata(file: Path, id3_separator: str = "/") -> Optional[Song]:
    """
    Get song based on the file metadata or file name

    ### Arguments
    - file: Path to file

    ### Returns
    - Song object
    """

    file_metadata = get_file_metadata(file, id3_separator)

    if file_metadata is None:
        return None

    return Song.from_missing_data(**file_metadata)


def gather_known_songs(output: str, output_format: str) -> Dict[str, List[Path]]:
    """
    Gather all known songs from the output directory

    ### Arguments
    - output: Output path template
    - output_format: Output format

    ### Returns
    - Dictionary containing all known songs and their paths
    """

    # Get the base directory from the path template
    # Path("/Music/test/{artist}/{artists} - {title}.{output-ext}") -> "/Music/test"
    base_dir = output.split("{", 1)[0]
    paths = Path(base_dir).glob(f"**/*.{output_format}")

    known_songs: Dict[str, List[Path]] = {}
    for path in paths:
        # Try to get the song from the metadata
        song = get_song_from_file_metadata(path)

        if song is None or song.url is None:
            continue

        known_paths = known_songs.get(song.url)
        if known_paths is None:
            known_songs[song.url] = [path]
        else:
            known_songs[song.url].append(path)

    return known_songs


def create_ytm_album(  # pylint: disable=unused-argument
    url: str, fetch_songs: bool = True
) -> Album:
    """
    Creates a list of Song objects from an album query.

    ### Arguments
    - album_query: the url of the album

    ### Returns
    - a list of Song objects
    """

    if "?list=" not in url or not url.startswith("https://music.youtube.com/"):
        raise ValueError(f"Invalid album url: {url}")

    browse_id = get_ytm_client().get_album_browse_id(
        url.split("?list=")[1].split("&")[0]
    )
    if browse_id is None:
        raise ValueError(f"Invalid album url: {url}")

    album = get_ytm_client().get_album(browse_id)

    if album is None:
        raise ValueError(f"Couldn't fetch album: {url}")

    metadata = {
        "artist": album["artists"][0]["name"],
        "name": album["title"],
        "url": url,
    }

    songs = []
    for track in album["tracks"]:
        artists = [artist["name"] for artist in track["artists"]]

        song = Song.from_missing_data(
            name=track["title"],
            artists=artists,
            artist=artists[0],
            album_name=metadata["name"],
            album_artist=metadata["artist"],
            duration=track["duration_seconds"],
            download_url=f"https://music.youtube.com/watch?v={track['videoId']}",
        )

        songs.append(song)

    return Album(**metadata, songs=songs, urls=[song.url for song in songs])


def create_ytm_playlist(  # pylint: disable=unused-argument
    url: str, fetch_songs: bool = True
) -> "SongList":
    """
    Returns a playlist object from a youtube playlist url

    ### Arguments
    - url: the url of the playlist

    ### Returns
    - a SongList-like object
    """

    from spotdl.types.playlist import (  # pylint: disable=import-outside-toplevel
        Playlist,
    )

    if not ("?list=" in url or "/browse/VLPL" in url) or not url.startswith(
        "https://music.youtube.com/"
    ):
        raise ValueError(f"Invalid playlist url: {url}")

    if "/browse/VLPL" in url:
        playlist_id = url.split("/browse/")[1]
    else:
        playlist_id = url.split("?list=")[1]
    playlist = get_ytm_client().get_playlist(playlist_id, None)  # type: ignore

    if playlist is None:
        raise ValueError(f"Couldn't fetch playlist: {url}")

    metadata = {
        "description": (
            playlist["description"] if playlist["description"] is not None else ""
        ),
        "author_url": (
            f"https://music.youtube.com/channel/{playlist['author']['id']}"
            if playlist.get("author") is not None
            else "Missing author url"
        ),
        "author_name": (
            playlist["author"]["name"]
            if playlist.get("author") is not None
            else "Missing author"
        ),
        "cover_url": (
            playlist["thumbnails"][0]["url"]
            if playlist.get("thumbnails") is not None
            else "Missing thumbnails"
        ),
        "name": playlist["title"],
        "url": url,
    }

    songs = []
    for track in playlist["tracks"]:
        if track["videoId"] is None or track["isAvailable"] is False:
            continue

        song = Song.from_missing_data(
            name=track["title"],
            artists=(
                [artist["name"] for artist in track["artists"]]
                if track.get("artists") is not None
                else []
            ),
            artist=(
                track["artists"][0]["name"]
                if track.get("artists") is not None
                else None
            ),
            album_name=(
                track.get("album", {}).get("name")
                if track.get("album") is not None
                else None
            ),
            duration=track.get("duration_seconds"),
            explicit=track.get("isExplicit"),
            download_url=f"https://music.youtube.com/watch?v={track['videoId']}",
        )

        songs.append(song)

    return Playlist(**metadata, songs=songs, urls=[song.url for song in songs])
