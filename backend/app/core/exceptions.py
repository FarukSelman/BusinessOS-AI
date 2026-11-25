from fastapi import HTTPException, status


class BadRequestException(HTTPException):
    """
    400 - Invalid request data
    """

    def __init__(
        self,
        detail: str = "Geçersiz istek.",
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class UnauthorizedException(HTTPException):
    """
    401 - Authentication required
    """

    def __init__(
        self,
        detail: str = "Bu işlem için giriş yapmalısınız.",
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )


class ForbiddenException(HTTPException):
    """
    403 - Authenticated but not allowed
    """

    def __init__(
        self,
        detail: str = "Bu işlem için yetkiniz yok.",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundException(HTTPException):
    """
    404 - Resource not found
    """

    def __init__(
        self,
        detail: str = "Kayıt bulunamadı.",
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ConflictException(HTTPException):
    """
    409 - Resource conflict
    """

    def __init__(
        self,
        detail: str = "Bu işlem mevcut kayıtlarla çakışıyor.",
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )