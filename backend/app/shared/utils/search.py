"""
Shared text search for list endpoints.

Postgres ILIKE under en_US collation does not match Turkish I/ı/İ ("IŞIK" does
not find "ışık"), so both the column and the search term are folded the same
way: I/İ/ı -> i and ş/ğ/ç/ö/ü -> s/g/c/o/u, then lower-cased. "ayse" therefore
also finds "Ayşe", which is how people type on phones.

Phone columns are additionally compared digit by digit, so "0555 123 45"
finds "05551234567".
"""
import re

from sqlalchemy import func, or_, select
from sqlalchemy.sql.elements import ColumnElement

_FOLD_FROM = "IİıŞşĞğÇçÖöÜü"
_FOLD_TO = "iiissggccoouu"
_FOLD_TABLE = str.maketrans(_FOLD_FROM, _FOLD_TO)

# A search term that looks like a phone number: digits plus common separators.
_PHONE_LIKE = re.compile(r"^[\d\s()+\-./]+$")
MIN_PHONE_DIGITS = 3


def fold_text(value: str) -> str:
    return value.translate(_FOLD_TABLE).lower()


def _folded(column) -> ColumnElement:
    return func.lower(func.translate(column, _FOLD_FROM, _FOLD_TO))


def _contains(term: str) -> str:
    """LIKE pattern that matches term literally (%, _ and \\ escaped)."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def text_search(term: str | None, *columns, phone_columns: tuple = ()) -> ColumnElement | None:
    """OR condition matching term in any column, or None when term is blank."""
    term = (term or "").strip()
    if not term:
        return None

    pattern = _contains(fold_text(term))
    conditions = [_folded(c).like(pattern, escape="\\") for c in (*columns, *phone_columns)]

    digits = re.sub(r"\D", "", term)
    if phone_columns and len(digits) >= MIN_PHONE_DIGITS and _PHONE_LIKE.match(term):
        conditions += [
            func.regexp_replace(c, r"\D", "", "g").like(f"%{digits}%") for c in phone_columns
        ]
    return or_(*conditions)


def count_rows(db, statement) -> int:
    """Total rows of a filtered SELECT, before ordering and paging."""
    return db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
