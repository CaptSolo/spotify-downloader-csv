from pathlib import Path

from spotdl.utils.metadata import download_cover_data


def test_download_cover_data_crops_with_ffmpeg(monkeypatch):
    class MockResponse:
        content = b"raw-image"

    def mock_get(*_args, **_kwargs):
        return MockResponse()

    def mock_run(command, check, stdout, stderr):
        output_file = Path(command[-1])
        output_file.write_bytes(b"square-image")
        return None

    monkeypatch.setattr("spotdl.utils.metadata.requests.get", mock_get)
    monkeypatch.setattr("spotdl.utils.metadata._get_cover_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr("spotdl.utils.metadata.subprocess.run", mock_run)

    assert download_cover_data("https://img.example/cover.jpg") == b"square-image"


def test_download_cover_data_returns_original_when_ffmpeg_fails(monkeypatch):
    class MockResponse:
        content = b"raw-image"

    def mock_get(*_args, **_kwargs):
        return MockResponse()

    def mock_run(*_args, **_kwargs):
        raise RuntimeError("ffmpeg failed")

    monkeypatch.setattr("spotdl.utils.metadata.requests.get", mock_get)
    monkeypatch.setattr("spotdl.utils.metadata._get_cover_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr("spotdl.utils.metadata.subprocess.run", mock_run)

    assert download_cover_data("https://img.example/cover.jpg") == b"raw-image"
