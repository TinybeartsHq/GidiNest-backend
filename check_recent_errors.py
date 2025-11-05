#!/usr/bin/env python
"""
Check recent errors from logs and database.
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

print('='*70)
print('RECENT API ERRORS (Last 1 hour)')
print('='*70)

# Get recent failed requests
since = datetime.now() - timedelta(hours=1)
recent_errors = ProviderRequestLog.objects.filter(
    provider_name="Embedly",
    success=False,
    created_at__gte=since
).order_by('-created_at')[:10]

if recent_errors.exists():
    print(f'\nFound {recent_errors.count()} failed Embedly requests:\n')
    for log in recent_errors:
        print(f"Time: {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Endpoint: {log.endpoint}")
        print(f"Method: {log.http_method}")
        print(f"Status Code: {log.response_status}")
        print(f"Error: {log.error_message}")

        if log.request_payload:
            print(f"Request: {log.request_payload}")

        if log.response_body:
            print(f"Response: {log.response_body}")

        print('-' * 70)
else:
    print('\nNo Embedly errors in last hour')

# Check for Payout/name-enquiry specifically
print('\n' + '='*70)
print('ACCOUNT VALIDATION ATTEMPTS (Payout/name-enquiry)')
print('='*70)

validation_logs = ProviderRequestLog.objects.filter(
    provider_name="Embedly",
    endpoint__contains="name-enquiry",
    created_at__gte=since
).order_by('-created_at')[:5]

if validation_logs.exists():
    print(f'\nFound {validation_logs.count()} validation attempts:\n')
    for log in validation_logs:
        status_icon = '✓' if log.success else '✗'
        print(f"{status_icon} {log.created_at.strftime('%H:%M:%S')} | "
              f"Status: {log.response_status} | "
              f"Success: {log.success}")

        if log.request_payload:
            print(f"   Request: {log.request_payload}")

        if not log.success:
            print(f"   Error: {log.error_message}")
            if log.response_body:
                print(f"   Response: {log.response_body}")
        print()
else:
    print('\nNo validation attempts in last hour')

print('='*70)
