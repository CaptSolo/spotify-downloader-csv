import pytest

from spotdl.utils.arguments import create_parser, parse_arguments


def test_parse_arguments():
    with pytest.raises(SystemExit):
        vars(parse_arguments())


def test_parse_cover_operation():
    args = create_parser().parse_args(["cover", "song.mp3"])

    assert args.operation == "cover"
    assert args.query == ["song.mp3"]


def test_parse_cover_remove_flag():
    args = create_parser().parse_args(["cover", "song.mp3", "--remove"])

    assert args.operation == "cover"
    assert args.query == ["song.mp3"]
    assert args.remove_cover is True


def test_parse_arguments_accepts_intermixed_cover_remove(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["spotdl", "cover", "--remove", "."],
    )

    args = parse_arguments()

    assert args.operation == "cover"
    assert args.query == ["."]
    assert args.remove_cover is True
