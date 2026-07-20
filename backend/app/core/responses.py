from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


# =====================================================
# Success Response
# =====================================================

class ApiResponse(
    BaseModel,
    Generic[T],
):
    """
    Standard API response wrapper.

    Example:

    {
        "success": true,
        "message": "Business created successfully.",
        "data": {}
    }
    """

    success: bool = True

    message: str

    data: T | None = None



# =====================================================
# Message Response
# =====================================================

class MessageResponse(BaseModel):
    """
    Response without data.

    Example:

    {
        "success": true,
        "message": "Deleted successfully."
    }
    """

    success: bool = True

    message: str



# =====================================================
# Error Response
# =====================================================

class ErrorResponse(BaseModel):
    """
    Standard error response.

    Example:

    {
        "success": false,
        "message": "Business not found.",
        "errors": []
    }
    """

    success: bool = False

    message: str

    errors: list[str] | None = None