import re
import unicodedata


def generate_slug(text: str) -> str:
    """
    Converts text into URL friendly slug.

    Example:

    Business OS AI

    ->

    business-os-ai
    """

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()

    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)

    return text.strip("-")