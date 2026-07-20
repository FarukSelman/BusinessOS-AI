from fastapi import APIRouter

"""
User Management Router.

Authentication endpoints are located under:

    /auth

Future endpoints:

    GET    /users
    GET    /users/{id}
    PATCH  /users/{id}
    DELETE /users/{id}
"""

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)