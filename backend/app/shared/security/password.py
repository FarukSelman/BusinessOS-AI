from passlib.context import CryptContext


pwd_context = CryptContext(
    schemes=[
        "bcrypt",
    ],
    deprecated="auto",
)



# ---------------------------------------------------------
# Hash Password
# ---------------------------------------------------------

def hash_password(
    password: str,
) -> str:

    return pwd_context.hash(
        password,
    )



# ---------------------------------------------------------
# Verify Password
# ---------------------------------------------------------

def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    try:

        return pwd_context.verify(
            plain_password,
            hashed_password,
        )

    except Exception:

        return False