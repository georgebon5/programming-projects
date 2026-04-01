"""Unit tests for app.utils.sanitize."""
import pytest

from app.utils.sanitize import sanitize_chat_message, sanitize_html


class TestSanitizeHtml:
    def test_strips_script_tags(self):
        result = sanitize_html("<script>alert('xss')</script>Hello")
        assert result == "alert('xss')Hello"

    def test_strips_nested_tags(self):
        result = sanitize_html("<b><i>text</i></b>")
        assert result == "text"

    def test_plain_text_unchanged(self):
        text = "What is machine learning?"
        assert sanitize_html(text) == text

    def test_strips_img_tag(self):
        result = sanitize_html('<img src="x" onerror="evil()">')
        assert result == ""

    def test_strips_anchor_tag_keeps_text(self):
        result = sanitize_html('<a href="http://evil.com">click here</a>')
        assert result == "click here"

    def test_empty_string(self):
        assert sanitize_html("") == ""

    def test_no_tags(self):
        text = "Normal text without any HTML."
        assert sanitize_html(text) == text


class TestSanitizeChatMessage:
    def test_strips_html_and_returns_clean_text(self):
        result = sanitize_chat_message("<script>alert('xss')</script>Hello")
        assert result == "alert('xss')Hello"

    def test_strips_nested_tags(self):
        result = sanitize_chat_message("<b><i>text</i></b>")
        assert result == "text"

    def test_normal_text_passes_through(self):
        text = "What is machine learning?"
        assert sanitize_chat_message(text) == text

    def test_trims_leading_trailing_whitespace(self):
        result = sanitize_chat_message("  hello world  ")
        assert result == "hello world"

    def test_trims_whitespace_with_html(self):
        result = sanitize_chat_message("  <b>bold</b>  ")
        assert result == "bold"

    def test_empty_message_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_chat_message("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_chat_message("   ")

    def test_html_only_raises(self):
        """Message containing only HTML tags becomes empty after stripping."""
        with pytest.raises(ValueError, match="cannot be empty"):
            sanitize_chat_message("<script></script>")

    def test_oversized_message_raises(self):
        long_msg = "a" * 101
        with pytest.raises(ValueError, match="exceeds maximum length"):
            sanitize_chat_message(long_msg, max_length=100)

    def test_message_at_exact_max_length_is_accepted(self):
        msg = "a" * 100
        result = sanitize_chat_message(msg, max_length=100)
        assert result == msg

    def test_default_max_length_allows_long_messages(self):
        msg = "a" * 9999
        result = sanitize_chat_message(msg)
        assert len(result) == 9999

    def test_custom_max_length(self):
        with pytest.raises(ValueError, match="exceeds maximum length of 50 characters"):
            sanitize_chat_message("a" * 51, max_length=50)
