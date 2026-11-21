from notes_agent.tools import count_words


def test_count_words():
    assert count_words("one two  three") == 3
