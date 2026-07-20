import re


def generate_slug(value: str) -> str:

    value = value.lower()

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