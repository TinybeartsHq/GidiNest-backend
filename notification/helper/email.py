import requests
from django.template.loader import render_to_string
from django.conf import settings

class MailClient:
    API_URL = "https://api.zeptomail.com/v1.1/email"

    def __init__(self, api_key: str = None, from_address: str = None):
        self.api_key = api_key or settings.ZEPTOMAIL_API_KEY
        self.from_address = from_address or settings.ZEPTOMAIL_FROM_EMAIL

        self.headers = {
            'accept': "application/json",
            'content-type': "application/json",
            'authorization': f"Zoho-enczapikey {self.api_key}",
        }

    def send_email(self, to_email, subject, template_name, context=None, to_name=None):
        context = context or {}
        try:
            html_body = render_to_string(template_name, context)

            payload = {
                "from": {"address": self.from_address},
                "to": [{"email_address": {"address": to_email, "name": to_name or to_email}}],
                "subject": subject,
                "htmlbody": html_body
            }

            response = requests.post(
                self.API_URL,
                json=payload,
                headers=self.headers
            )
            print(response.text)  # For debugging purposes

            if response.status_code != 201:
                raise Exception(f"ZeptoMail error: {response.status_code} - {response.text}")

            return response.json()
        except Exception as e:
            #TODO handle logging or re-raise the exception
            print(f"Error sending email: {e}")
            pass