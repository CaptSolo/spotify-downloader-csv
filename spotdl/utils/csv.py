"""
Module for parsing Chosic-format CSV playlist files into Song objects.
"""

import csv
import logging
from pathlib import Path
from typing import List

from spotdl.types.song import Song

__all__ = ["parse_csv", "CSVError"]

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"Song", "Artist", "Duration", "Spotify Track Id", "ISRC"}


class CSVError(Exception):
    """
    Base class for all exceptions related to CSV parsing.
    """


def _parse_duration(duration_str: str) -> int:
    """
    Parse MM:SS duration string to seconds.

    ### Arguments
    - duration_str: Duration in MM:SS format.

    ### Returns
    - Duration in seconds.
    """

    parts = duration_str.strip().split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    raise CSVError(f"Invalid duration format: {duration_str}")


def parse_csv(file_path: str) -> List[Song]:
    """
    Parse a Chosic-format CSV file and return a list of Song objects.

    ### Arguments
    - file_path: Path to the CSV file.

    ### Returns
    - List of Song objects.
    """

    path = Path(file_path)
    if not path.exists():
        raise CSVError(f"CSV file not found: {file_path}")

    with open(path, "r", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise CSVError(f"CSV file has no headers: {file_path}")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise CSVError(
                f"CSV file is missing required columns: {', '.join(sorted(missing))}"
            )

        rows = list(reader)

    if not rows:
        raise CSVError(f"CSV file has no data rows: {file_path}")

    total_tracks = len(rows)
    songs: List[Song] = []

    for row in rows:
        name = row["Song"].strip().strip('"')
        artists_raw = row["Artist"].strip().strip('"')
        artists = [a.strip() for a in artists_raw.split(",")]
        duration = _parse_duration(row["Duration"])
        song_id = row["Spotify Track Id"].strip()
        isrc = row["ISRC"].strip() or None

        album_name = row.get("Album", "").strip().strip('"') or "Unknown Album"
        album_date = row.get("Album Date", "").strip()
        year = int(album_date[:4]) if album_date and len(album_date) >= 4 else 0
        date = album_date if album_date else ""

        genres_raw = row.get("Genres", "").strip().strip('"')
        genres = (
            [g.strip() for g in genres_raw.split(",") if g.strip()]
            if genres_raw
            else []
        )

        popularity_raw = row.get("Popularity", "").strip()
        popularity = int(popularity_raw) if popularity_raw else None

        list_position_raw = row.get("#", "").strip()
        list_position = int(list_position_raw) if list_position_raw else None

        song = Song(
            name=name,
            artists=artists,
            artist=artists[0],
            genres=genres,
            disc_number=1,
            disc_count=1,
            album_name=album_name,
            album_artist=artists[0],
            duration=duration,
            year=year,
            date=date,
            track_number=list_position if list_position else 0,
            tracks_count=total_tracks,
            song_id=song_id,
            explicit=False,
            publisher="",
            url=f"https://open.spotify.com/track/{song_id}",
            isrc=isrc,
            cover_url=None,
            copyright_text=None,
            popularity=popularity,
            list_position=list_position,
            list_length=total_tracks,
        )

        songs.append(song)

    logger.info("Parsed %d songs from CSV file: %s", len(songs), file_path)

    return songs
