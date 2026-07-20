from app.modules.user.repository import UserRepository


class UserService:
    """
    User management service.

    Authentication işlemleri AuthService tarafından yürütülür.
    """

    def __init__(
        self,
        repository: UserRepository,
    ):
        self.repository = repository