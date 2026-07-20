from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import ErrorResponse


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
                f"{field}: {error['msg']}"
            )


        response = ErrorResponse(
            message="Validation failed.",
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
            message="Internal server error.",
            errors=None,
        )

        return JSONResponse(
            status_code=500,
            content=response.model_dump(),
        )