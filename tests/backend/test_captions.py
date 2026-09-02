from backend.app.captions import STYLE_ORDER, STYLES, build_ass
from backend.app.schemas import Segment, WordTiming


def _segment_with_words(text: str, start: float, words: list[str], word_dur: float = 0.3) -> Segment:
    timings = []
    t = start
    for w in words:
        timings.append(WordTiming(word=w, start=t, end=t + word_dur))
        t += word_dur
    return Segment(id=0, start=start, end=t, text=text, words=timings)


def test_all_styles_are_registered_in_order():
    assert set(STYLE_ORDER) == set(STYLES.keys())
    assert len(STYLE_ORDER) == 6


def test_line_style_emits_one_dialogue_per_segment():
    seg = _segment_with_words("ola mundo", 0.0, ["ola", "mundo"])
    ass = build_ass([seg], "editorial", 1080, 1920)
    assert ass.count("Dialogue:") == 1
    assert "ola mundo" in ass


def test_impacto_style_uppercases_text():
    seg = _segment_with_words("compraste um porsche", 0.0, ["compraste", "um", "porsche"])
    ass = build_ass([seg], "impacto", 1080, 1920)
    assert "COMPRASTE UM PORSCHE" in ass


def test_karaoke_style_emits_k_tags_per_word():
    seg = _segment_with_words("ola mundo bonito", 0.0, ["ola", "mundo", "bonito"])
    ass = build_ass([seg], "karaoke", 1080, 1920)
    assert ass.count("\\k") == 3


def test_uma_palavra_style_emits_one_dialogue_per_word():
    seg = _segment_with_words("ola mundo bonito", 0.0, ["ola", "mundo", "bonito"])
    ass = build_ass([seg], "uma_palavra", 1080, 1920)
    assert ass.count("Dialogue:") == 3
    assert "OLA" in ass and "MUNDO" in ass and "BONITO" in ass


def test_word_mode_falls_back_to_line_when_words_missing():
    seg = Segment(id=0, start=0.0, end=1.0, text="sem palavras", words=[])
    ass = build_ass([seg], "karaoke", 1080, 1920)
    assert ass.count("Dialogue:") == 1
    assert "sem palavras" in ass


def test_special_characters_are_escaped():
    seg = Segment(id=0, start=0.0, end=1.0, text="isto {parece} uma variavel", words=[])
    ass = build_ass([seg], "discreto", 1080, 1920)
    assert "{parece}" not in ass
    assert "(parece)" in ass
