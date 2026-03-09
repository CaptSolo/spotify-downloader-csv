from spotdl.types.song import Song
from spotdl.utils.downloader import find_musicbrainz_cover_url, pick_thumbnail_url


def test_pick_thumbnail_url_prefers_square_non_webp():
    thumbnails = [
        {"url": "https://img.example/landscape.jpg", "width": 1280, "height": 720},
        {"url": "https://img.example/square.webp", "width": 1000, "height": 1000},
        {"url": "https://img.example/square.jpg", "width": 800, "height": 800},
    ]

    assert pick_thumbnail_url(thumbnails) == "https://img.example/square.jpg"


def test_find_musicbrainz_cover_url_uses_best_release(monkeypatch):
    song = Song.from_missing_data(
        name="Moments",
        artist="Lost Identities",
        artists=["Lost Identities"],
        album_name="Moments",
        year=2023,
        isrc="TEST12345678",
    )

    class MockResponse:
        def __init__(self, payload):
            self.payload = payload

        def json(self):
            return self.payload

        def raise_for_status(self):
            return None

    def mock_get(url, **_kwargs):
        if "musicbrainz.org" in url:
            return MockResponse(
                {
                    "recordings": [
                        {
                            "releases": [
                                {
                                    "id": "release-one",
                                    "title": "Moments",
                                    "status": "Official",
                                    "date": "2023-06-01",
                                },
                                {
                                    "id": "release-two",
                                    "title": "Moments Remix",
                                    "status": "Official",
                                    "date": "2023-06-02",
                                },
                            ]
                        }
                    ]
                }
            )

        if "release-one" in url:
            return MockResponse(
                {
                    "images": [
                        {
                            "front": True,
                            "thumbnails": {
                                "500": "https://cover.example/release-one-500.jpg"
                            },
                        }
                    ]
                }
            )

        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("spotdl.utils.downloader.requests.get", mock_get)

    assert (
        find_musicbrainz_cover_url(song) == "https://cover.example/release-one-500.jpg"
    )
