# notifications/utils.py

from firebase_admin import messaging
from notification.lib.firebase import firebase_admin  # Ensure firebase is initialized
from account.models.users import UserModel
from account.models import UserDevices


def send_push_notification_to_user(user: UserModel, title: str, message: str):
    """
    Sends a push notification to all active devices of a given user.
    """
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
            print(f"Notification sent to device {device.device_id} — Response: {response}")

        except Exception as e:
            print(f"Failed to send notification to device {device.device_id} — Error: {e}")


