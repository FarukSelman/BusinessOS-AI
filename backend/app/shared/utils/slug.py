import re

# Turkish letters would otherwise be dropped ("Güzellik" -> "gzellik").
TRANSLITERATION = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i", "İ": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
    "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u", "Û": "u",
})


def generate_slug(value: str) -> str:

    value = value.translate(TRANSLITERATION).lower()

    value = re.sub(
        r"[^a-z0-9\s-]",
        "",
        value,
    )

    value = re.sub(
        r"\s+",
        "-",
        value,
    )

    value = re.sub(
        r"-+",
        "-",
        value,
    )

    return value.strip("-")
