import re


class TextChunker:
    """Sentence-aware text chunker for RAG.
    
    Splits text at sentence boundaries instead of
    arbitrary character positions, preserving semantic
    coherence within each chunk.
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
        sentences = [s.strip() for s in sentences if s.strip()]

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

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks