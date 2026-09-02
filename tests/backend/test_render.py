from backend.app.render import _escape_ffmpeg_path, render_micro_variation
from video_variator.effects import VariationParams


def test_escape_ffmpeg_path_wraps_and_escapes():
    assert _escape_ffmpeg_path("/tmp/plain.ttf") == "'/tmp/plain.ttf'"
    assert _escape_ffmpeg_path("/tmp/it's.ttf") == "'/tmp/it\\'s.ttf'"
    assert _escape_ffmpeg_path("C:/font.ttf") == "'C\\:/font.ttf'"


def test_render_micro_variation_raises_without_ffmpeg(monkeypatch):
    monkeypatch.setattr("backend.app.render.shutil.which", lambda _: None)
    params = VariationParams(
        title="", speed=1.0, brightness=0.0, contrast=1.0, saturation=1.0,
        hue_deg=0.0, crop_fraction=0.0, mirror=False,
    )
    try:
        render_micro_variation("in.mp4", "out.mp4", params)
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "ffmpeg" in str(exc)
