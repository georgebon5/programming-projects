"""Input sanitization utilities."""
import re


def sanitize_html(text: str) -> str:
    """Strip all HTML tags from user input."""
    # Use regex to strip HTML tags - avoids adding bleach dependency
    clean = re.sub(r'<[^>]+>', '', text)
    return clean


def sanitize_chat_message(content: str, max_length: int = 10000) -> str:
    """Sanitize chat message content.

    - Strips HTML tags
    - Trims whitespace
    - Enforces max length

    Raises ValueError if message is empty or too long after sanitization.
    """
    content = sanitize_html(content)
    content = content.strip()

    if not content:
        raise ValueError("Message cannot be empty")

    if len(content) > max_length:
        raise ValueError(f"Message exceeds maximum length of {max_length} characters")

    return content
