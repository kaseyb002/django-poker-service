from rest_framework.response import Response
from rest_framework import status

def bad_request(explanation):
    return Response(status=status.HTTP_400_BAD_REQUEST, data={"detail": explanation})

def unauthorized(explanation):
    return Response(status=status.HTTP_401_UNAUTHORIZED, data={"detail": explanation})

def not_found(explanation):
    return Response(status=status.HTTP_404_NOT_FOUND, data={"detail": explanation})

def missing_parameter(parameter_name):
    return bad_request("Missing " + parameter_name + " parameter.")

def user_not_in_table():
    return unauthorized("User not in table.")

def user_is_banned():
    return unauthorized("User is banned from this table.")

def user_lacks_permission():
    return unauthorized("User does not have permission for this action.")

def no_admins_remaining():
    return bad_request("No other admins remaining.")
