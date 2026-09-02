from backend.app.music import build_duck_filter, merge_windows
from backend.app.schemas import Segment


def test_merge_windows_joins_close_segments():
    merged = merge_windows([(0.0, 1.0), (1.2, 2.0), (5.0, 6.0)], merge_gap=0.3)
    assert merged == [(0.0, 2.0), (5.0, 6.0)]


def test_merge_windows_keeps_far_apart_segments_separate():
    merged = merge_windows([(0.0, 1.0), (3.0, 4.0)], merge_gap=0.3)
    assert merged == [(0.0, 1.0), (3.0, 4.0)]


def test_merge_windows_empty_input():
    assert merge_windows([]) == []


def test_build_duck_filter_returns_anull_without_segments():
    assert build_duck_filter([]) == "anull"


def test_build_duck_filter_includes_between_terms_for_each_window():
    segments = [
        Segment(id=0, start=0.0, end=1.0, text="a", words=[]),
        Segment(id=1, start=5.0, end=6.0, text="b", words=[]),
    ]
    filt = build_duck_filter(segments, duck_level=0.2)
    assert filt.startswith("volume=eval=frame:volume=")
    assert filt.count("between(t,") == 2
    assert "0.200" in filt
