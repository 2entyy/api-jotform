import random

from video_variator.effects import build_filter_complex, random_variation_params


def test_random_variation_params_within_ranges():
    rng = random.Random(0)
    params = random_variation_params(rng, "TITLE", allow_mirror=True)
    assert 0.96 <= params.speed <= 1.06
    assert -0.03 <= params.brightness <= 0.03
    assert 0.95 <= params.contrast <= 1.05
    assert 0.9 <= params.saturation <= 1.1
    assert -6.0 <= params.hue_deg <= 6.0
    assert 0.0 <= params.crop_fraction <= 0.03


def test_random_variation_params_mirror_disabled_by_default():
    rng = random.Random(0)
    params = random_variation_params(rng, "TITLE")
    assert params.mirror is False


def test_build_filter_complex_includes_expected_filters():
    rng = random.Random(0)
    params = random_variation_params(rng, "TITLE")
    filt = build_filter_complex(
        params, font_path="/tmp/font.ttf", fontsize=40, textfile="/tmp/t.txt"
    )
    assert "drawtext" in filt
    assert "setpts=PTS/" in filt
    assert "eq=brightness=" in filt
    assert "[0:v]" in filt and "[0:a]" in filt
    assert "[v]" in filt and "[a]" in filt


def test_build_filter_complex_skips_crop_when_zero():
    rng = random.Random(1)
    params = random_variation_params(rng, "TITLE", crop_range=(0.0, 0.0))
    filt = build_filter_complex(
        params, font_path="/tmp/font.ttf", fontsize=40, textfile="/tmp/t.txt"
    )
    assert "crop=" not in filt
