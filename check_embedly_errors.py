#!/usr/bin/env python
"""
Check recent Embedly API errors from the database logs.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gidinest_backend.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from providers.models import ProviderRequestLog
from datetime import datetime, timedelta

print('='*60)
print('EMBEDLY API ERROR ANALYSIS')
print('='*60)

# Get recent failed Embedly requests (last 24 hours)
since = datetime.now() - timedelta(hours=24)
recent_errors = ProviderRequestLog.objects.filter(
    provider_name="Embedly",
    success=False,
    created_at__gte=since
).order_by('-created_at')[:20]

print(f'\nFound {recent_errors.count()} failed Embedly requests in last 24 hours')
print(f'Showing most recent 20:\n')

for log in recent_errors:
    print(f"Time: {log.created_at}")
    print(f"Endpoint: {log.endpoint}")
    print(f"Method: {log.http_method}")
    print(f"Status: {log.response_status}")
    print(f"Error Message: {log.error_message}")

    if log.response_body:
        print(f"Response: {log.response_body}")

    print('-' * 60)

# Check for get_customer endpoint specifically
get_customer_errors = ProviderRequestLog.objects.filter(
    provider_name="Embedly",
    endpoint__contains="customers/",
    http_method="GET",
    success=False,
    created_at__gte=since
)

print(f'\n\nSpecific GET customer errors: {get_customer_errors.count()}')

if get_customer_errors.exists():
    print('\nSample error details:')
    sample = get_customer_errors.first()
    print(f"  Status Code: {sample.response_status}")
    print(f"  Error: {sample.error_message}")
    print(f"  Response Body: {sample.response_body}")
    print(f"  Request Payload: {sample.request_payload}")

# Check Embedly API configuration
from django.conf import settings
print('\n' + '='*60)
print('EMBEDLY API CONFIGURATION')
print('='*60)
print(f"API Key configured: {'Yes' if settings.EMBEDLY_API_KEY_PRODUCTION else 'No'}")
print(f"Organization ID configured: {'Yes' if settings.EMBEDLY_ORGANIZATION_ID_PRODUCTION else 'No'}")

if settings.EMBEDLY_API_KEY_PRODUCTION:
    key_preview = settings.EMBEDLY_API_KEY_PRODUCTION[:10] + '...' if len(settings.EMBEDLY_API_KEY_PRODUCTION) > 10 else 'too short'
    print(f"API Key preview: {key_preview}")
