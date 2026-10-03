import os
from app.modules.document.processing.cleaner import TextCleaner
from app.modules.document.processing.chunker import TextChunker
from app.modules.document.processing.extractor import PDFExtractor
from app.modules.document.processing.txt_extractor import TxtExtractor
from app.modules.document.processing.docx_extractor import DocxExtractor


class DocumentProcessor:

    EXTRACTORS = {
        '.pdf': PDFExtractor,
        '.txt': TxtExtractor,
        '.docx': DocxExtractor,
        '.doc': DocxExtractor,
    }

    @staticmethod
    def process(path: str) -> list[str]:
        ext = os.path.splitext(path)[1].lower()
        extractor_class = DocumentProcessor.EXTRACTORS.get(ext)

        if extractor_class is None:
            raise ValueError(f"Desteklenmeyen dosya formatı: {ext}")

        text = extractor_class.extract(path)
        text = TextCleaner.clean(text)
        chunks = TextChunker.chunk(text)
        return chunks