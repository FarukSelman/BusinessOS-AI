import re


class TextChunker:
    """Sentence-aware text chunker for RAG.
    
    Splits text at sentence boundaries instead of
    arbitrary character positions, preserving semantic
    coherence within each chunk. A single sentence longer
    than chunk_size (a list or table with no punctuation)
    is cut into chunk_size windows that share `overlap`
    characters, so no chunk outgrows the embedding input.
    """

    SENTENCE_ENDINGS = re.compile(
        r'(?<=[.!?。？！])\s+'
    )

    @staticmethod
    def chunk(
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[str]:

        sentences = TextChunker.SENTENCE_ENDINGS.split(text)
        sentences = [
            piece
            for s in sentences if s.strip()
            for piece in TextChunker._windows(s.strip(), chunk_size, overlap)
        ]

        if not sentences:
            return [text] if text.strip() else []

        chunks = []
        current_chunk: list[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Build overlap from end of current chunk
                overlap_chunk: list[str] = []
                overlap_length = 0

                for s in reversed(current_chunk):
                    if overlap_length + len(s) > overlap:
                        break
                    overlap_chunk.insert(0, s)
                    overlap_length += len(s)

                current_chunk = overlap_chunk
                current_length = overlap_length

                # The overlap must not push the next chunk past chunk_size.
                if current_length + sentence_length > chunk_size:
                    current_chunk, current_length = [], 0

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    @staticmethod
    def _windows(sentence: str, chunk_size: int, overlap: int) -> list[str]:
        """The sentence itself, or chunk_size windows of it when it is too long."""
        if len(sentence) <= chunk_size:
            return [sentence]
        step = chunk_size - overlap if 0 <= overlap < chunk_size else chunk_size
        windows = []
        for start in range(0, len(sentence), step):
            windows.append(sentence[start:start + chunk_size])
            if start + chunk_size >= len(sentence):
                break
        return windows