import fitz


class PDFExtractor:

    @staticmethod
    def extract(path: str) -> str:

        document = fitz.open(path)

        pages = []

        for page in document:
            pages.append(page.get_text())

        document.close()

        return "\n".join(pages)