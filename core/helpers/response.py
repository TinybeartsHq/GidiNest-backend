from django.http import JsonResponse
from rest_framework import status


def error_response(message='An error occurred', errors=None, status_code=400):
    response_data = {'status': False, 'message': message, 'detail': message,'errors': errors}
    return JsonResponse(response_data, status=status_code)


def validation_error_response(errors=None):
    message = "validation failed"
    response_data = {'status': False,'message': message, 'detail': message, 'errors': errors}
    return JsonResponse(response_data, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


def success_response(data=None, message='Success', status_code=200):
    response_data = {'status': True, 'message': message,'detail': message, 'data': data}
    return JsonResponse(response_data, status=status_code)


def bad_request_response(message='Bad Request', status_code=400):
    return error_response(message, None, status_code)


def notfound_request_response(message='Resource could not be located'):
    return error_response(message, None, 404)


def unauthorized_response(message="You don't have authorization to access this resource"):
    return error_response(message, None, status.HTTP_401_UNAUTHORIZED)


def internal_server_error_response(message='Internal Server Error', status_code=500):
    return error_response(message, None, status_code)
