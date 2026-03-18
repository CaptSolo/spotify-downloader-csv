from spotdl.types.song import Song
from spotdl.utils.metadata import remove_cover_file, update_cover_file


class FakeID3(dict):
    def getall(self, key):
        return [self["APIC:Cover"]] if key == "APIC" and "APIC:Cover" in self else []

    def delall(self, key):
        if key == "APIC":
            self.pop("APIC:Cover", None)
            self.pop("APIC", None)

    def save(self, *args, **kwargs):
        self.saved_args = args
        self.saved_kwargs = kwargs


def test_update_cover_file_updates_mp3(monkeypatch, tmp_path):
    fake_id3 = FakeID3({"APIC:Cover": "old-cover"})

    monkeypatch.setattr(
        "spotdl.utils.metadata.download_cover_data",
        lambda *_: b"new-cover-data",
    )
    monkeypatch.setattr("spotdl.utils.metadata.ID3", lambda *_: fake_id3)

    song = Song.from_missing_data(
        name="Song Name",
        artist="Artist Name",
        artists=["Artist Name"],
        cover_url="https://img.example/cover.jpg",
    )

    assert update_cover_file(tmp_path / "song.mp3", song) is True
    assert "APIC:Cover" not in fake_id3
    assert fake_id3["APIC"].data == b"new-cover-data"
    assert fake_id3.saved_kwargs == {"v2_version": 3}


def test_update_cover_file_returns_false_without_cover_url(tmp_path):
    song = Song.from_missing_data(
        name="Song Name",
        artist="Artist Name",
        artists=["Artist Name"],
    )

    assert update_cover_file(tmp_path / "song.mp3", song) is False


def test_remove_cover_file_removes_mp3(monkeypatch, tmp_path):
    fake_id3 = FakeID3({"APIC:Cover": "old-cover"})

    monkeypatch.setattr("spotdl.utils.metadata.ID3", lambda *_: fake_id3)

    assert remove_cover_file(tmp_path / "song.mp3") is True
    assert "APIC:Cover" not in fake_id3
    assert fake_id3.saved_kwargs == {"v2_version": 3}


def test_remove_cover_file_returns_false_when_missing_mp3_cover(monkeypatch, tmp_path):
    fake_id3 = FakeID3()

    monkeypatch.setattr("spotdl.utils.metadata.ID3", lambda *_: fake_id3)

    assert remove_cover_file(tmp_path / "song.mp3") is False
