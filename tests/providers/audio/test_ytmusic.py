import pytest

from spotdl.providers.audio import YouTubeMusic
from spotdl.types.result import Result
from spotdl.types.song import Song


@pytest.mark.vcr()
def test_ytm_search():
    provider = YouTubeMusic()

    assert (
        provider.search(
            Song.from_dict(
                {
                    "name": "Nobody Else",
                    "artists": ["Abstrakt"],
                    "artist": "Abstrakt",
                    "album_id": "0kx3ml8bdAYrQtcIwvkhp8",
                    "album_name": "Nobody Else",
                    "album_artist": "Abstrakt",
                    "album_type": "album",
                    "genres": [],
                    "disc_number": 1,
                    "disc_count": 1,
                    "duration": 162.406,
                    "year": 2022,
                    "date": "2022-03-17",
                    "track_number": 1,
                    "tracks_count": 1,
                    "isrc": "GB2LD2210007",
                    "song_id": "0kx3ml8bdAYrQtcIwvkhp8",
                    "cover_url": "https://i.scdn.co/image/ab67616d0000b27345f5ba253b9825efc88bc236",
                    "explicit": False,
                    "publisher": "NCS",
                    "url": "https://open.spotify.com/track/0kx3ml8bdAYrQtcIwvkhp8",
                    "copyright_text": "2022 NCS",
                    "download_url": None,
                }
            )
        )
        is not None
    )


@pytest.mark.vcr()
def test_ytm_get_results():
    provider = YouTubeMusic()

    results = provider.get_results("Lost Identities Moments")

    assert len(results) > 3
    assert any(result.album_id for result in results if result.verified)


def test_ytm_get_cover_url_prefers_album_art(monkeypatch):
    provider = YouTubeMusic()
    song = Song.from_missing_data(
        name="Moments",
        artist="Lost Identities",
        artists=["Lost Identities"],
    )
    result = Result(
        source="YouTubeMusic",
        url="https://music.youtube.com/watch?v=test",
        verified=True,
        name="Moments",
        duration=180,
        author="Lost Identities",
        result_id="test",
        album="Moments",
        album_id="MPREtest",
    )

    monkeypatch.setattr(
        provider.client,
        "get_album",
        lambda _album_id: {
            "thumbnails": [
                {
                    "url": "https://img.example/landscape.jpg",
                    "width": 1280,
                    "height": 720,
                },
                {
                    "url": "https://img.example/square.jpg",
                    "width": 1024,
                    "height": 1024,
                },
            ]
        },
    )

    assert provider.get_cover_url(song, result) == "https://img.example/square.jpg"


def test_ytm_get_cover_url_searches_song_results(monkeypatch):
    provider = YouTubeMusic()
    song = Song.from_missing_data(
        name="Moments",
        artist="Lost Identities",
        artists=["Lost Identities"],
        isrc="TEST12345678",
        album_name="Moments",
    )
    result = Result(
        source="YouTube",
        url="https://www.youtube.com/watch?v=test",
        verified=False,
        name="Moments",
        duration=180,
        author="Lost Identities",
        result_id="test",
    )

    monkeypatch.setattr(
        provider,
        "get_results",
        lambda *_args, **_kwargs: [
            Result(
                source="YouTubeMusic",
                url="https://music.youtube.com/watch?v=song",
                verified=True,
                name="Moments",
                duration=180,
                author="Lost Identities",
                result_id="song",
                album="Moments",
                album_id="MPREsearch",
            )
        ],
    )
    monkeypatch.setattr(
        provider.client,
        "get_album",
        lambda _album_id: {
            "thumbnails": [
                {
                    "url": "https://img.example/cover.jpg",
                    "width": 1200,
                    "height": 1200,
                }
            ]
        },
    )

    assert provider.get_cover_url(song, result) == "https://img.example/cover.jpg"
