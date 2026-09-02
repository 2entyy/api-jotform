from backend.app.critic import score_hook
from backend.app.schemas import Segment


def _seg(text: str, start: float, end: float) -> Segment:
    return Segment(id=0, start=start, end=end, text=text, words=[])


def test_curiosity_and_contrast_boost_score():
    segments = [_seg("Vocês pensavam que eu tinha comprado um Porsche, mas não, comprei uma lambreta", 0.0, 4.0)]
    result = score_hook(segments)
    assert result.score >= 7
    assert "gancho de curiosidade" in result.summary
    assert "contraste" in result.summary


def test_generic_opening_scores_lower_and_gets_suggestions():
    segments = [_seg("hoje vou mostrar como se faz um bolo de chocolate", 0.0, 4.0)]
    result = score_hook(segments)
    assert result.score < 7
    assert result.suggestions


def test_empty_opening_scores_minimum():
    result = score_hook([])
    assert result.score == 1
    assert any("Sem fala" in s for s in result.suggestions)


def test_question_and_number_each_add_a_point():
    with_extras = score_hook([_seg("sabias que 5 em cada 10 pessoas fazem isto?", 0.0, 4.0)])
    without_extras = score_hook([_seg("sabias que muita gente faz isto", 0.0, 4.0)])
    assert with_extras.score > without_extras.score
