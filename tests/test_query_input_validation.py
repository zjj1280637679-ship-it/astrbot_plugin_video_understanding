from astrbot_plugin_video_understanding.tool import parse_video_index


def test_video_index_accepts_integer_values():
    assert parse_video_index(0) == 0
    assert parse_video_index(2) == 2
    assert parse_video_index(" 3 ") == 3


def test_video_index_rejects_ambiguous_values():
    for value in (True, False, 1.9, "1.0", "-1", None):
        assert parse_video_index(value) is None
