class TxtExtractor:
    @staticmethod
    def extract(path: str) -> str:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
