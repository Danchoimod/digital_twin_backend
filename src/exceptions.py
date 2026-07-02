from fastapi import HTTPException, status


class CustomBaseException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundException(CustomBaseException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class AuthenticationException(CustomBaseException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class GCPIntegrationException(CustomBaseException):
    def __init__(self, detail: str = "GCP service integration error"):
        super().__init__(detail=detail, status_code=status.HTTP_502_BAD_GATEWAY)
