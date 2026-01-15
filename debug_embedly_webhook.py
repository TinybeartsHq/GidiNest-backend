#!/usr/bin/env python3
"""
Temporary debug script to test Embedly webhook signatures
Usage: python debug_embedly_webhook.py

This helps diagnose why webhook signatures are failing
"""
import hashlib
import hmac
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gidinest_backend.settings')
django.setup()

from django.conf import settings

print("=" * 80)
print("EMBEDLY WEBHOOK SIGNATURE DEBUG TOOL")
print("=" * 80)

# Get the secret from settings
secret = settings.EMBEDLY_API_KEY_PRODUCTION

print(f"\nSecret configured: {secret[:10]}...{secret[-10:]} (length: {len(secret)} chars)")
print("\nNOTE: Paste the actual signature and body from the next webhook failure")
print("\nTo get these values:")
print("1. Wait for next deposit attempt (or ask user to try again)")
print("2. Check logs: sudo journalctl -u gunicorn -n 100 | grep -A 5 'signature mismatch'")
print("3. Paste the X-Auth-Signature header and body here")
print("\n" + "=" * 80)

# Example test payload
test_payload = {
    "event": "nip",
    "data": {
        "accountNumber": "9710306989",
        "reference": "TEST_REF_001",
        "amount": 10000,
        "senderName": "Faithfulness Ekeh",
        "senderBank": "Test Bank"
    }
}

import json
payload_json = json.dumps(test_payload, separators=(',', ':'))
body_bytes = payload_json.encode('utf-8')

print("\nTEST PAYLOAD:")
print(payload_json)
print("\n" + "=" * 80)
print("EXPECTED SIGNATURES FOR TEST PAYLOAD")
print("=" * 80)

# SHA-512 (Embedly's documented method)
sha512_sig = hmac.new(secret.encode('utf-8'), body_bytes, hashlib.sha512).hexdigest()
print(f"\nSHA-512: {sha512_sig}")

# SHA-256 (fallback)
sha256_sig = hmac.new(secret.encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
print(f"SHA-256: {sha256_sig}")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("\n1. Contact Embedly support with these details:")
print(f"   - Your API key: {secret[:10]}...{secret[-10:]}")
print("   - Test payload above")
print("   - Expected signatures above")
print("   - Ask them to verify the webhook secret")
print("\n2. Or manually test with a real webhook:")
print("   - Get X-Auth-Signature header from logs")
print("   - Get request body from logs")
print("   - Run this script with actual values")
print("\n3. Temporary workaround: Disable signature verification")
print("   (NOT RECOMMENDED for production, but can confirm this is the issue)")
