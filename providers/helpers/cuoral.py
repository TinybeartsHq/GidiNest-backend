import requests
import json
from django.conf import settings


class CuoralAPI:
    """
    Helper class for integrating with Cuoral's messaging API.
    """

    BASE_URL = "https://api.cuoral.com/external/v1"
    SMS_ENDPOINT = "/external/v1/sms/send"

    def __init__(self):
        self.api_key = getattr(settings, "CUORAL_API_KEY", None)
        if not self.api_key:
            raise ValueError("Cuoral API Key is not set in Django settings (CUORAL_API_KEY)")

        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
        }
    

    def normalize_nigerian_phone(self,phone: str) -> str:
        """
        Converts Nigerian phone number to international format.
        
        Example:
            08083848362 -> 2348083848362
            +2348083848362 -> 2348083848362

        Args:
            phone (str): Raw phone number input

        Returns:
            str: Formatted phone number in international format
        """
        if not phone:
            return ""

        # Remove all non-numeric characters
        digits = ''.join(filter(str.isdigit, phone))

        # Handle formats
        if digits.startswith("234") and len(digits) == 13:
            return digits
        elif digits.startswith("0") and len(digits) == 11:
            return "+234" + digits[1:]
        elif len(digits) == 10:  # Edge case: someone types just 8083848362
            return "234" + digits
        elif digits.startswith("234") and len(digits) > 13:
            return digits[:13]  # Truncate any extra digits
        else:
            return digits  # fallback


    def send_sms(self, to: str, message: str, sender_id: str = "Gidinest", channel: str = "generic") -> dict:
        """
        Sends an SMS using Cuoral's API.

        Args:
            to (str): Recipient's phone number in international format (e.g. 2348101234567)
            message (str): The message content.
            sender_id (str): Optional sender ID (default: 'Cuoral')
            channel (str): Optional channel (default: 'dnd')

        Returns:
            dict: Response from Cuoral API or error details.
        """
        url = f"{self.BASE_URL}{self.SMS_ENDPOINT}"
        payload = {
            "sender_id": sender_id,
            "channel": channel,
            "to": self.normalize_nigerian_phone(to),
            "message": message,
        }

        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(payload), timeout=30)
            response.raise_for_status()

            return {
                "status": "success",
                "data": response.json()
            }

        except requests.exceptions.HTTPError as http_err:
            error_details = ""
            try:
                if 'response' in locals() and response is not None:
                    error_details = response.text
            except (ValueError, AttributeError):
                pass
            return {
                "status": "error",
                "message": f"An error occurred please try again later",
                "details": error_details
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "An error occurred please try again later"
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Cuoral API request timed out"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "An error occurred please try again later"
            }
