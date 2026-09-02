"""Background-music ducking (quieter under speech) and optional beat detection."""
from __future__ import annotations

from typing import List, Tuple

from backend.app.schemas import Segment


def merge_windows(windows: List[Tuple[float, float]], merge_gap: float = 0.3) -> List[Tuple[float, float]]:
    if not windows:
        return []
    ordered = sorted(windows)
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start - last_end <= merge_gap:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def build_duck_filter(segments: List[Segment], duck_level: float = 0.15) -> str:
    """ffmpeg `volume` expression: full volume by default, dips to duck_level
    while any (merged) speech window is playing."""
    windows = merge_windows([(s.start, s.end) for s in segments])
    if not windows:
        return "anull"
    terms = "*".join(
        f"if(between(t,{start:.3f},{end:.3f}),{duck_level:.3f},1)" for start, end in windows
    )
    return f"volume=eval=frame:volume='{terms}'"


def detect_beats(audio_path: str) -> List[float]:
    """Beat timestamps (seconds), best-effort. Returns [] if librosa isn't
    installed or analysis fails — beat markers are a nice-to-have, not a
    dependency the rest of the app needs."""
    try:
        import librosa
    except ImportError:
        return []
    try:
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        _tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        return [float(t) for t in librosa.frames_to_time(beat_frames, sr=sr)]
    except Exception:
        return []
