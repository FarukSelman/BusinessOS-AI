from app.modules.document.processing.cleaner import TextCleaner
from app.modules.document.processing.chunker import TextChunker
from app.modules.document.processing.extractor import PDFExtractor


class DocumentProcessor:

    @staticmethod
    def process(path: str) -> list[str]:

        text = PDFExtractor.extract(path)

        text = TextCleaner.clean(text)

        chunks = TextChunker.chunk(text)

        return chunks