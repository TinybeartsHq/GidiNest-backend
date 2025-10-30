import requests
import logging
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)

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
        """
        Send an email using ZeptoMail API.

        Returns:
            dict: {'status': 'success', 'data': response_data} on success
                  {'status': 'error', 'message': error_message} on failure
        """
        context = context or {}
        try:
            # Render email template
            try:
                html_body = render_to_string(template_name, context)
            except Exception as template_error:
                error_msg = f"Failed to render email template '{template_name}': {str(template_error)}"
                logger.error(error_msg)
                return {'status': 'error', 'message': error_msg}

            payload = {
                "from": {"address": self.from_address},
                "to": [{"email_address": {"address": to_email, "name": to_name or to_email}}],
                "subject": subject,
                "htmlbody": html_body
            }

            # Send email via ZeptoMail API
            response = requests.post(
                self.API_URL,
                json=payload,
                headers=self.headers,
                timeout=10  # Add timeout to prevent hanging
            )

            logger.info(f"ZeptoMail API response for {to_email}: Status {response.status_code}")

            if response.status_code == 201:
                logger.info(f"Email sent successfully to {to_email} - Subject: {subject}")
                return {'status': 'success', 'data': response.json()}
            else:
                error_msg = f"ZeptoMail API error: {response.status_code} - {response.text}"
                logger.error(f"Failed to send email to {to_email}: {error_msg}")
                return {'status': 'error', 'message': error_msg}

        except requests.exceptions.Timeout:
            error_msg = "Email service timeout - request took too long"
            logger.error(f"Timeout sending email to {to_email}: {error_msg}")
            return {'status': 'error', 'message': error_msg}

        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to email service"
            logger.error(f"Connection error sending email to {to_email}: {error_msg}")
            return {'status': 'error', 'message': error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.exception(f"Exception sending email to {to_email}: {error_msg}")
            return {'status': 'error', 'message': error_msg}