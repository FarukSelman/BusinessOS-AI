from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import ErrorResponse


# Turkish text for the common Pydantic error types, keyed by error["type"];
# {placeholders} come from error["ctx"]. Types not listed keep Pydantic's
# English message.
VALIDATION_MESSAGES_TR = {
    "missing": "Bu alan zorunlu.",
    "string_type": "Metin olmalı.",
    "string_too_short": "En az {min_length} karakter olmalı.",
    "string_too_long": "En fazla {max_length} karakter olabilir.",
    "too_short": "En az {min_length} öğe olmalı.",
    "too_long": "En fazla {max_length} öğe olabilir.",
    "int_type": "Tam sayı olmalı.",
    "int_parsing": "Tam sayı olmalı.",
    "int_from_float": "Tam sayı olmalı.",
    "float_type": "Sayı olmalı.",
    "float_parsing": "Sayı olmalı.",
    "decimal_type": "Sayı olmalı.",
    "decimal_parsing": "Sayı olmalı.",
    "bool_type": "Evet/hayır (true/false) olmalı.",
    "bool_parsing": "Evet/hayır (true/false) olmalı.",
    "greater_than": "{gt} değerinden büyük olmalı.",
    "greater_than_equal": "En az {ge} olmalı.",
    "less_than": "{lt} değerinden küçük olmalı.",
    "less_than_equal": "En fazla {le} olabilir.",
    "date_type": "Geçerli bir tarih girin (YYYY-AA-GG).",
    "date_parsing": "Geçerli bir tarih girin (YYYY-AA-GG).",
    "date_from_datetime_parsing": "Geçerli bir tarih girin (YYYY-AA-GG).",
    "time_type": "Geçerli bir saat girin (SS:DD).",
    "time_parsing": "Geçerli bir saat girin (SS:DD).",
    "datetime_type": "Geçerli bir tarih ve saat girin.",
    "datetime_parsing": "Geçerli bir tarih ve saat girin.",
    "datetime_from_date_parsing": "Geçerli bir tarih ve saat girin.",
    "uuid_type": "Geçersiz kimlik (UUID).",
    "uuid_parsing": "Geçersiz kimlik (UUID).",
    "enum": "Şunlardan biri olmalı: {expected}.",
    "literal_error": "Şunlardan biri olmalı: {expected}.",
    "url_type": "Geçerli bir adres (URL) girin.",
    "url_parsing": "Geçerli bir adres (URL) girin.",
    "json_invalid": "Gönderilen veri geçerli JSON değil.",
}


def validation_message_tr(error: dict) -> str:
    """One Pydantic error as a Turkish sentence (English when the type is unknown)."""
    kind = error.get("type", "")
    message = str(error.get("msg", ""))
    if kind == "value_error":
        # e-mail fields, and our own validators' ValueError text (already Turkish)
        if "valid email" in message:
            return "Geçerli bir e-posta adresi girin."
        return message.removeprefix("Value error, ")
    template = VALIDATION_MESSAGES_TR.get(kind)
    if template is None:
        return message
    try:
        return template.format(**(error.get("ctx") or {}))
    except (KeyError, IndexError):
        return message


def register_exception_handlers(
    app: FastAPI,
) -> None:


    # =====================================================
    # HTTP Exceptions
    # =====================================================

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):

        response = ErrorResponse(
            message=str(exc.detail),
            errors=None,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=response.model_dump(),
            headers=getattr(exc, "headers", None),  # e.g. Retry-After on 429
        )


    # =====================================================
    # Validation Errors
    # =====================================================

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):

        errors = []

        for error in exc.errors():

            field = ".".join(
                str(item)
                for item in error["loc"]
            )

            errors.append(
                f"{field}: {validation_message_tr(error)}"
            )


        response = ErrorResponse(
            message="Girilen bilgiler geçersiz.",
            errors=errors,
        )

        return JSONResponse(
            status_code=422,
            content=response.model_dump(),
        )


    # =====================================================
    # Unexpected Exceptions
    # =====================================================

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ):

        # TODO:
        # Production ortamında burada logger kullanılacak.
        # Örn:
        # logger.exception(exc)

        response = ErrorResponse(
            message="Beklenmeyen bir hata oluştu.",
            errors=None,
        )

        return JSONResponse(
            status_code=500,
            content=response.model_dump(),
        )