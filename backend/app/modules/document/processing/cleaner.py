import re


class TextCleaner:

    @staticmethod
    def clean(text: str) -> str:

        text = text.replace("\x00", "")

        text = re.sub(
            r"\n{2,}",
            "\n",
            text,
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        return text.strip()