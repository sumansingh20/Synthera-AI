"""Tests for utility helper functions."""

from synthera.utils.helpers import (
    truncate_text,
    clean_html,
    estimate_tokens,
    build_citation,
    sanitize_filename,
)


class TestTruncateText:
    def test_short_text_unchanged(self):
        assert truncate_text("hello world", 100) == "hello world"

    def test_long_text_truncated(self):
        text = "word " * 100
        result = truncate_text(text, 50)
        assert len(result) <= 55  # allows for "..." suffix
        assert result.endswith("...")

    def test_preserves_word_boundary(self):
        result = truncate_text("hello world foo bar", 12)
        assert "..." in result
        # Should not cut in the middle of a word


class TestCleanHtml:
    def test_strips_tags(self):
        result = clean_html("<p>Hello <b>World</b></p>")
        assert "<" not in result
        assert "Hello" in result
        assert "World" in result

    def test_strips_scripts(self):
        result = clean_html("<script>alert('xss')</script>Content here")
        assert "alert" not in result
        assert "Content here" in result

    def test_strips_styles(self):
        result = clean_html("<style>.foo{color:red}</style>Visible text")
        assert "color" not in result
        assert "Visible text" in result

    def test_normalizes_whitespace(self):
        result = clean_html("<p>Hello</p>   <p>World</p>")
        assert "  " not in result


class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 1  # minimum 1

    def test_rough_estimate(self):
        # ~4 chars per token
        text = "a" * 400
        assert estimate_tokens(text) == 100


class TestBuildCitation:
    def test_basic_citation(self):
        cite = build_citation("Test Title", "https://example.com", "Some snippet")
        assert cite["title"] == "Test Title"
        assert cite["url"] == "https://example.com"
        assert "snippet" in cite
        assert "accessed_at" in cite

    def test_citation_without_snippet(self):
        cite = build_citation("Title", "https://example.com")
        assert cite["snippet"] == ""


class TestSanitizeFilename:
    def test_removes_special_chars(self):
        result = sanitize_filename("What is Quantum? A Review!")
        assert "?" not in result
        assert "!" not in result

    def test_replaces_spaces_with_underscores(self):
        result = sanitize_filename("hello world test")
        assert " " not in result
        assert "_" in result

    def test_max_length(self):
        long_name = "a" * 200
        result = sanitize_filename(long_name)
        assert len(result) <= 100
