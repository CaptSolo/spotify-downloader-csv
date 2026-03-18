import asyncio
from types import SimpleNamespace

from spotdl.console.cover import cover


class DummyDownloader:
    def __init__(
        self,
        remove_cover=False,
        search_result_response=None,
        resolve_cover_result=None,
    ):
        self.settings = {"id3_separator": "/", "remove_cover": remove_cover}
        self.semaphore = asyncio.Semaphore(1)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._search_result_response = search_result_response
        self._resolve_cover_result = resolve_cover_result

    def search_result(self, _song):
        if isinstance(self._search_result_response, Exception):
            raise self._search_result_response

        if self._search_result_response is None:
            raise LookupError("No result configured")

        return self._search_result_response

    def _resolve_cover_url(self, song, matched_result):
        if callable(self._resolve_cover_result):
            return self._resolve_cover_result(song, matched_result)

        if self._resolve_cover_result is not None:
            return self._resolve_cover_result

        return f"https://img.example/{song.name}.jpg"


def test_cover_updates_existing_file(monkeypatch, tmp_path):
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"audio")

    monkeypatch.setattr(
        "spotdl.console.cover.get_file_metadata",
        lambda *_: {
            "name": "Song Name",
            "artist": "Artist Name",
            "artists": ["Artist Name"],
            "album_name": "Album Name",
            "isrc": "TEST12345678",
        },
    )

    captured = {}

    def mock_update_cover_file(file_path, song):
        captured["file_path"] = file_path
        captured["cover_url"] = song.cover_url
        captured["artist"] = song.artist
        return True

    monkeypatch.setattr("spotdl.console.cover.update_cover_file", mock_update_cover_file)

    downloader = DummyDownloader()

    try:
        cover([str(audio_file)], downloader)
    finally:
        downloader.loop.close()
        asyncio.set_event_loop(None)

    assert captured == {
        "file_path": audio_file,
        "cover_url": "https://img.example/Song Name.jpg",
        "artist": "Artist Name",
    }


def test_cover_uses_matched_result_for_cover_resolution(monkeypatch, tmp_path):
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"audio")

    monkeypatch.setattr(
        "spotdl.console.cover.get_file_metadata",
        lambda *_: {
            "name": "Song Name",
            "artist": "Artist Name",
            "artists": ["Artist Name"],
        },
    )

    captured = {}

    def mock_update_cover_file(file_path, song):
        captured["file_path"] = file_path
        captured["cover_url"] = song.cover_url
        return True

    monkeypatch.setattr("spotdl.console.cover.update_cover_file", mock_update_cover_file)

    matched_result = SimpleNamespace(album_id="album-123")
    downloader = DummyDownloader(
        search_result_response=("https://download.example/song", object(), matched_result),
        resolve_cover_result=lambda _song, result: (
            f"https://img.example/{result.album_id}.jpg" if result else None
        ),
    )

    try:
        cover([str(audio_file)], downloader)
    finally:
        downloader.loop.close()
        asyncio.set_event_loop(None)

    assert captured == {
        "file_path": audio_file,
        "cover_url": "https://img.example/album-123.jpg",
    }


def test_cover_uses_thumbnail_fallback_when_cover_resolution_fails(
    monkeypatch, tmp_path
):
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"audio")

    monkeypatch.setattr(
        "spotdl.console.cover.get_file_metadata",
        lambda *_: {
            "name": "Song Name",
            "artist": "Artist Name",
            "artists": ["Artist Name"],
            "download_url": "https://download.example/song",
        },
    )

    captured = {}

    def mock_update_cover_file(file_path, song):
        captured["file_path"] = file_path
        captured["cover_url"] = song.cover_url
        return True

    monkeypatch.setattr("spotdl.console.cover.update_cover_file", mock_update_cover_file)

    provider = SimpleNamespace(
        get_download_metadata=lambda *_args, **_kwargs: {
            "thumbnails": [
                {
                    "url": "https://img.example/landscape.jpg",
                    "width": 1280,
                    "height": 720,
                },
                {
                    "url": "https://img.example/square.jpg",
                    "width": 500,
                    "height": 500,
                },
            ]
        }
    )

    downloader = DummyDownloader(
        search_result_response=("https://download.example/song", provider, object()),
        resolve_cover_result=lambda *_args: None,
    )

    try:
        cover([str(audio_file)], downloader)
    finally:
        downloader.loop.close()
        asyncio.set_event_loop(None)

    assert captured == {
        "file_path": audio_file,
        "cover_url": "https://img.example/square.jpg",
    }


def test_cover_removes_existing_file_cover(monkeypatch, tmp_path):
    audio_file = tmp_path / "test.mp3"
    audio_file.write_bytes(b"audio")

    get_metadata_called = {"value": False}

    def mock_get_file_metadata(*_args, **_kwargs):
        get_metadata_called["value"] = True
        return {}

    monkeypatch.setattr("spotdl.console.cover.get_file_metadata", mock_get_file_metadata)

    captured = {}

    def mock_remove_cover_file(file_path):
        captured["file_path"] = file_path
        return True

    monkeypatch.setattr("spotdl.console.cover.remove_cover_file", mock_remove_cover_file)

    downloader = DummyDownloader(remove_cover=True)

    try:
        cover([str(audio_file)], downloader)
    finally:
        downloader.loop.close()
        asyncio.set_event_loop(None)

    assert captured == {"file_path": audio_file}
    assert get_metadata_called["value"] is False
