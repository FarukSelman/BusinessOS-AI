from docx import Document

class DocxExtractor:
    @staticmethod
    def extract(path: str) -> str:
        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
