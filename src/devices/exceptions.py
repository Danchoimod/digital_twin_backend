from fastapi import HTTPException, status


class DeviceNotFoundException(HTTPException):
    def __init__(self, device_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with ID '{device_id}' not found",
        )


class DeviceAlreadyExistsException(HTTPException):
    def __init__(self, device_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with device_id '{device_id}' already registered",
        )
