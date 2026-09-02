from backend.app.assistant import parse_command


def test_remove_music_command():
    action = parse_command("tira a música por favor")
    assert action.action == "remove_music"


def test_strengthen_hook_command():
    action = parse_command("quero um gancho mais forte")
    assert action.action == "strengthen_hook"


def test_speed_up_command():
    action = parse_command("acelera um bocadinho")
    assert action.action == "speed_up"


def test_slow_down_command():
    action = parse_command("abranda a velocidade")
    assert action.action == "slow_down"


def test_set_caption_style_command_extracts_style():
    action = parse_command("muda para o estilo karaoke")
    assert action.action == "set_caption_style"
    assert action.params["style"] == "karaoke"


def test_set_caption_style_with_multiword_style():
    action = parse_command("põe o estilo uma palavra")
    assert action.action == "set_caption_style"
    assert action.params["style"] == "uma_palavra"


def test_unrecognized_command_without_llm_falls_back_to_unknown():
    action = parse_command("faz-me um sanduiche")
    assert action.action == "unknown"
    assert action.message
