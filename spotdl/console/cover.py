"""
Cover refresh module for the console.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

from spotdl.download.downloader import Downloader
from spotdl.providers.audio import AudioProvider, Piped
from spotdl.types.song import Song
from spotdl.utils.ffmpeg import FFMPEG_FORMATS
from spotdl.utils.downloader import pick_thumbnail_url
from spotdl.utils.metadata import get_file_metadata, remove_cover_file, update_cover_file

__all__ = ["cover"]

logger = logging.getLogger(__name__)


def _collect_audio_paths(query: List[str]) -> List[Path]:
    """
    Collect supported audio files from a list of files and directories.
    """

    paths: List[Path] = []
    for path in query:
        test_path = Path(path)
        if not test_path.exists():
            logger.error("Path does not exist: %s", path)
            continue

        if test_path.is_dir():
            for out_format in FFMPEG_FORMATS:
                paths.extend(test_path.glob(f"*.{out_format}"))
        elif test_path.is_file():
            if test_path.suffix.split(".")[-1] not in FFMPEG_FORMATS:
                logger.error("File is not a supported audio format: %s", path)
                continue

            paths.append(test_path)

    return paths


def _build_song_from_file_metadata(
    song_meta: Optional[Dict[str, object]],
) -> Optional[Song]:
    """
    Build a minimally hydrated song object for cover art resolution.
    """

    if song_meta is None:
        return None

    song_data = dict(song_meta)
    artist = song_data.get("artist")
    artists = song_data.get("artists") or []

    if not isinstance(artists, list):
        artists = [artists] if artists else []

    if artist is None and artists:
        artist = artists[0]

    if not artists and artist:
        artists = [artist]

    if song_data.get("name") is None or artist is None or not artists:
        return None

    song_data["artist"] = artist
    song_data["artists"] = artists
    song_data["cover_url"] = None

    return Song.from_missing_data(**song_data)


def _create_metadata_provider(downloader: Downloader, download_url: str):
    """
    Create an audio provider suitable for fetching provider metadata only.
    """

    provider_type = (
        Piped
        if "piped.video/" in download_url
        or downloader.settings["audio_providers"][0] == "piped"
        else AudioProvider
    )

    return provider_type(
        output_format=downloader.settings["format"],
        cookie_file=downloader.settings["cookie_file"],
        search_query=downloader.settings["search_query"],
        filter_results=downloader.settings["filter_results"],
        yt_dlp_args=downloader.settings["yt_dlp_args"],
    )


def cover(query: List[str], downloader: Downloader) -> None:
    """
    Refresh album cover art for existing local audio files.

    ### Arguments
    - query: list of file or directory paths.
    - downloader: Already initialized downloader instance.
    """

    paths = _collect_audio_paths(query)
    remove_cover = downloader.settings.get("remove_cover", False)

    def process_file(file: Path):
        if remove_cover:
            try:
                removed = remove_cover_file(file)
            except Exception as exc:  # pragma: no cover - defensive logging path
                logger.debug("Could not remove cover art for %s: %s", file.name, exc)
                removed = False

            if not removed:
                logger.error("Could not remove cover art for %s", file.name)
                return None

            logger.info("Removed cover art for %s", file.name)
            return None

        song_meta = get_file_metadata(file, downloader.settings["id3_separator"])
        song = _build_song_from_file_metadata(song_meta)

        if song is None:
            logger.error("Could not determine song metadata for %s", file.name)
            return None

        matched_result = None
        matched_provider = None
        download_url = song.download_url

        try:
            download_url, matched_provider, matched_result = downloader.search_result(song)
        except Exception as exc:
            logger.debug("Could not rematch %s for cover refresh: %s", file.name, exc)

        try:
            song.cover_url = downloader._resolve_cover_url(song, matched_result)
        except Exception as exc:  # pragma: no cover - defensive logging path
            logger.debug("Could not resolve cover art for %s: %s", file.name, exc)
            song.cover_url = None

        if song.cover_url is None and download_url:
            metadata_provider = matched_provider or _create_metadata_provider(
                downloader, download_url
            )

            try:
                download_info = metadata_provider.get_download_metadata(
                    download_url, download=False
                )
            except Exception as exc:  # pragma: no cover - defensive logging path
                logger.debug(
                    "Could not fetch download metadata for %s: %s", file.name, exc
                )
                download_info = None

            if download_info is not None:
                song.cover_url = pick_thumbnail_url(download_info.get("thumbnails"))
                if song.cover_url is None:
                    song.cover_url = download_info.get("thumbnail")

        if song.cover_url is None:
            logger.error("Could not find cover art for %s", file.name)
            return None

        try:
            updated = update_cover_file(file, song)
        except Exception as exc:  # pragma: no cover - defensive logging path
            logger.debug("Could not update cover art for %s: %s", file.name, exc)
            updated = False

        if not updated:
            logger.error("Could not update cover art for %s", file.name)
            return None

        logger.info("Updated cover art for %s", file.name)
        return None

    async def pool_worker(file_path: Path) -> None:
        async with downloader.semaphore:
            await downloader.loop.run_in_executor(None, process_file, file_path)

    tasks = [pool_worker(path) for path in paths]
    downloader.loop.run_until_complete(asyncio.gather(*tasks))
