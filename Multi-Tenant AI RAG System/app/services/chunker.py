"""
Text chunking with overlap for RAG.
Uses tiktoken for accurate token counting.
"""

import tiktoken


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    model: str = "cl100k_base",
) -> list[str]:
    """
    Split text into overlapping chunks based on token count.

    Args:
        text: The full text to chunk.
        chunk_size: Max tokens per chunk.
        chunk_overlap: Overlapping tokens between consecutive chunks.
        model: Tiktoken encoding name.

    Returns:
        List of text chunks.
    """
    enc = tiktoken.get_encoding(model)
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text_str = enc.decode(chunk_tokens)
        chunks.append(chunk_text_str)

        if end >= len(tokens):
            break
        start += chunk_size - chunk_overlap

    return chunks
