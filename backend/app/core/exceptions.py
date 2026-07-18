from fastapi import HTTPException, status


class BadRequestException(HTTPException):

    def __init__(
        self,
        detail: str,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class UnauthorizedException(HTTPException):

    def __init__(
        self,
        detail: str = "Unauthorized.",
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )