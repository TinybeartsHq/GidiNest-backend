import firebase_admin
from firebase_admin import credentials, messaging
import os
from django.conf import settings

# Initialize Firebase only if credentials file exists
_firebase_app = None
try:
    # Try to get Firebase credentials path from settings or environment
    firebase_cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    if not firebase_cred_path:
        firebase_cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'xxxxxxx.json')
    
    if os.path.exists(firebase_cred_path):
        cred = credentials.Certificate(firebase_cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
    else:
        # Firebase not configured - app can still run without push notifications
        _firebase_app = None
except Exception as e:
    # Firebase initialization failed - app can still run without push notifications
    _firebase_app = None

# Export firebase_admin module for use in other files
# This allows push.py to import messaging even if Firebase isn't initialized