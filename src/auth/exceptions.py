from src.exceptions import AuthenticationException


class InvalidCredentialsException(AuthenticationException):
    def __init__(self, detail: str = "Invalid username or password"):
        super().__init__(detail=detail)


class TokenExpiredException(AuthenticationException):
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail=detail)
