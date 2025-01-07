from rest_framework.exceptions import APIException
from rest_framework import status

class PokerServiceError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ('Malformed request.')
    default_code = 'parse_error'