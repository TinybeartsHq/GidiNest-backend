# notifications/utils.py
import logging

from account.models.users import UserModel
from account.models import UserDevices

logger = logging.getLogger(__name__)

# Optional Firebase import - handle gracefully if not configured
try:
    from firebase_admin import messaging
    import firebase_admin
    # Check if Firebase is initialized
    try:
        firebase_admin.get_app()
        FIREBASE_AVAILABLE = True
    except ValueError:
        # Firebase not initialized
        FIREBASE_AVAILABLE = False
except (ImportError, Exception):
    FIREBASE_AVAILABLE = False


def send_push_notification_to_user(user: UserModel, title: str, message: str):
    """
    Sends a push notification to all active devices of a given user.
    """
    if not FIREBASE_AVAILABLE:
        return  # Silently skip if Firebase is not configured
    
    devices = UserDevices.objects.filter(
        user=user, active=True
    ).exclude(fcm_token__isnull=True).exclude(fcm_token__exact='')

    for device in devices:
        try:
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message,
                ),
                token=device.fcm_token,
                android=messaging.AndroidConfig(priority="high"),
                apns=messaging.APNSConfig(
                    headers={"apns-priority": "10"},
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=message,
                            ),
                            sound="default"  # plays the default notification sound on iOS
                        )
                    )
                )
            )

            response = messaging.send(fcm_message)
            logger.info(f"Notification sent to device {device.device_id}")

        except Exception as e:
            logger.error(f"Failed to send notification to device {device.device_id}: {e}")


