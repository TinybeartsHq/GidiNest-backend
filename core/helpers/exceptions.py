"""
Custom exception handler for DRF to return consistent error format
"""
from rest_framework.views import exception_handler
from rest_framework import status
from django.http import JsonResponse


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns errors in the API's standard format
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize the response data
        custom_response_data = {
            'status': False,
            'message': 'An error occurred',
            'detail': 'An error occurred',
            'errors': {}
        }
        
        # Handle authentication errors
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            # Handle both dict and string response.data
            if isinstance(response.data, dict):
                detail = response.data.get('detail', 'Authentication credentials were not provided.')
            else:
                detail = str(response.data)
            
            if 'Authentication credentials were not provided' in str(detail):
                custom_response_data['message'] = 'Authentication required. Please include the access token in the Authorization header as: Authorization: Bearer <your_access_token>'
                custom_response_data['detail'] = 'Authentication required. Please include the access token in the Authorization header as: Authorization: Bearer <your_access_token>'
                custom_response_data['errors'] = {
                    'authorization': 'Missing or invalid Authorization header. Expected format: Authorization: Bearer <access_token>'
                }
            elif 'Token is invalid' in str(detail) or 'Token is expired' in str(detail) or 'token_not_valid' in str(detail):
                custom_response_data['message'] = 'Invalid or expired token. Please refresh your token.'
                custom_response_data['detail'] = 'Invalid or expired token. Please refresh your token.'
            else:
                custom_response_data['message'] = str(detail)
                custom_response_data['detail'] = str(detail)
        # Handle permission errors
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            if isinstance(response.data, dict):
                detail = response.data.get('detail', 'You do not have permission to perform this action.')
            else:
                detail = str(response.data)
            custom_response_data['message'] = str(detail)
            custom_response_data['detail'] = str(detail)
        # Handle validation errors
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = 'Validation failed'
            custom_response_data['detail'] = 'Validation failed'
            custom_response_data['errors'] = response.data
        # Handle not found errors
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            if isinstance(response.data, dict):
                detail = response.data.get('detail', 'Resource not found.')
            else:
                detail = str(response.data)
            custom_response_data['message'] = str(detail)
            custom_response_data['detail'] = str(detail)
        # Handle other errors
        else:
            if isinstance(response.data, dict):
                if 'detail' in response.data:
                    custom_response_data['message'] = str(response.data['detail'])
                    custom_response_data['detail'] = str(response.data['detail'])
                else:
                    custom_response_data['errors'] = response.data
            else:
                custom_response_data['message'] = str(response.data)
                custom_response_data['detail'] = str(response.data)
        
        response.data = custom_response_data
    
    return response

