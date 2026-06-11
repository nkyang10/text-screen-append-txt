from text_dedup import TextDeduplicator


def test_empty_string_returns_none():
    d = TextDeduplicator()
    assert d.get_new_text("") is None


def test_whitespace_only_returns_none():
    d = TextDeduplicator()
    assert d.get_new_text("   \n  \t  ") is None


def test_first_text_returns_cleaned_text():
    d = TextDeduplicator()
    result = d.get_new_text("  hello world  ")
    assert result == "hello world"


def test_exact_duplicate_returns_none():
    d = TextDeduplicator()
    d.get_new_text("hello world")
    assert d.get_new_text("hello world") is None


def test_fuzzy_near_duplicate_returns_only_new_lines():
    d = TextDeduplicator(threshold=0.5)
    d.get_new_text("hello world\nhow are you")
    result = d.get_new_text("hello world\nhow are you\nnew line")
    assert result == "new line"


def test_completely_new_text_returns_fully():
    d = TextDeduplicator()
    d.get_new_text("first text here")
    result = d.get_new_text("completely different text")
    assert result == "completely different text"


def test_reset_clears_state():
    d = TextDeduplicator()
    d.get_new_text("hello world")
    d.reset()
    result = d.get_new_text("hello world")
    assert result == "hello world"


def test_window_size_evicts_old_entries():
    d = TextDeduplicator(window_size=2)
    d.get_new_text("one")
    d.get_new_text("two")
    d.get_new_text("three")
    assert list(d._history) == ["two", "three"]


def test_threshold_one_exact_matches_skipped():
    d = TextDeduplicator(threshold=1.0)
    d.get_new_text("hello")
    assert d.get_new_text("hello") is None


def test_threshold_one_non_exact_returns_fresh():
    d = TextDeduplicator(threshold=1.0)
    d.get_new_text("hello")
    result = d.get_new_text("hello world")
    assert result == "hello world"


def test_threshold_zero_different_text_returns_fresh():
    d = TextDeduplicator(threshold=0.0)
    d.get_new_text("abc")
    result = d.get_new_text("abd")
    assert result == "abd"


def test_multi_line_inter_line_duplicates_deduped():
    d = TextDeduplicator()
    result = d.get_new_text("line1\nline1\nline2\nline1")
    assert result == "line1\nline2"


def test_whitespace_insensitive_matching():
    d = TextDeduplicator()
    d.get_new_text("  hello world  ")
    assert d.get_new_text("hello world") is None


def test_fresh_lines_returns_only_unseen_lines():
    d = TextDeduplicator()
    d.get_new_text("line1\nline2")
    result = d._fresh_lines("line2\nline3")
    assert result == ["line3"]


def test_clean_strips_whitespace_and_removes_duplicate_lines():
    d = TextDeduplicator()
    result = d._clean("  a  \n  a  \n  b  ")
    assert result == "a\nb"
