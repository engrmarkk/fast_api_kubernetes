from fastapi import HTTPException
from fastapi import status


class NoUserDataHTTPException(HTTPException):
    def __init__(self, detail: str, complete_registration: bool):
        super().__init__(status_code=status.HTTP_200_OK, detail=detail)
        self.complete_registration = complete_registration
