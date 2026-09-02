from video_variator.titles import extract_keywords, generate_titles, wrap_text


def test_extract_keywords_filters_stopwords_and_ranks_by_frequency():
    text = "o carro vermelho e o carro azul estavam parados o carro vermelho partiu"
    keywords = extract_keywords(text, "pt", top_n=2)
    assert keywords[0] == "carro"


def test_generate_titles_returns_requested_count():
    titles = generate_titles("this is a video about cooking pasta", "en", 4, seed=1)
    assert len(titles) == 4
    assert all(isinstance(t, str) and t for t in titles)


def test_generate_titles_is_deterministic_with_seed():
    a = generate_titles("texto de exemplo sobre viagens", "pt", 3, seed=42)
    b = generate_titles("texto de exemplo sobre viagens", "pt", 3, seed=42)
    assert a == b


def test_generate_titles_falls_back_to_pt_for_unknown_language():
    titles = generate_titles("algum texto", "xx", 2, seed=0)
    assert len(titles) == 2


def test_generate_titles_handles_empty_transcript():
    titles = generate_titles("", "pt", 3, seed=0)
    assert len(titles) == 3


def test_wrap_text_breaks_long_lines():
    wrapped = wrap_text("uma frase bastante longa para testar o wrap automatico", max_chars=15)
    assert all(len(line) <= 20 for line in wrapped.split("\n"))
