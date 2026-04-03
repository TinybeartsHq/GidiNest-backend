# providers/helpers/paystack.py
"""
Paystack API integration for GidiNest gifting flow.

Handles:
- Transaction initialization (card/bank/USSD payments)
- Transaction verification
- Transfer recipient creation
- Bank transfers (disbursements)
- Webhook signature verification
"""
import hmac
import hashlib
import logging
import requests
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)

PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaystackAPI:
    """Client for Paystack REST API."""

    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        if not self.secret_key:
            raise ValueError("PAYSTACK_SECRET_KEY is not configured")
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Transaction (gift payments)
    # ------------------------------------------------------------------

    def initialize_transaction(self, amount_naira, email, callback_url, metadata=None, reference=None):
        """
        Initialize a Paystack transaction.

        Args:
            amount_naira: Amount in Naira (Decimal/float) — converted to kobo internally
            email: Contributor's email (required by Paystack)
            callback_url: URL to redirect after payment
            metadata: Dict with fund_token, contributor_name, etc.
            reference: Optional unique reference (Paystack generates one if omitted)

        Returns:
            dict: {authorization_url, access_code, reference} on success
            None on failure
        """
        amount_kobo = int(Decimal(str(amount_naira)) * 100)

        payload = {
            "amount": amount_kobo,
            "email": email,
            "currency": "NGN",
            "callback_url": callback_url,
        }
        if metadata:
            payload["metadata"] = metadata
        if reference:
            payload["reference"] = reference

        try:
            resp = requests.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize",
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            data = resp.json()

            if data.get("status") is True:
                logger.info(f"Paystack transaction initialized: {data['data']['reference']}")
                return data["data"]
            else:
                logger.error(f"Paystack initialize failed: {data.get('message')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Paystack initialize request error: {e}")
            return None

    def verify_transaction(self, reference):
        """
        Verify a Paystack transaction by reference.

        Returns:
            dict: Full transaction data on success (status, amount, metadata, etc.)
            None on failure
        """
        try:
            resp = requests.get(
                f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                headers=self.headers,
                timeout=30,
            )
            data = resp.json()

            if data.get("status") is True:
                return data["data"]
            else:
                logger.error(f"Paystack verify failed for {reference}: {data.get('message')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Paystack verify request error: {e}")
            return None

    # ------------------------------------------------------------------
    # Transfers (disbursements / withdrawals)
    # ------------------------------------------------------------------

    def create_transfer_recipient(self, name, account_number, bank_code):
        """
        Create a Paystack transfer recipient (mother's bank account).

        Returns:
            dict: {recipient_code, ...} on success
            None on failure
        """
        payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN",
        }

        try:
            resp = requests.post(
                f"{PAYSTACK_BASE_URL}/transferrecipient",
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            data = resp.json()

            if data.get("status") is True:
                logger.info(f"Paystack recipient created: {data['data']['recipient_code']}")
                return data["data"]
            else:
                logger.error(f"Paystack create recipient failed: {data.get('message')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Paystack create recipient request error: {e}")
            return None

    def initiate_transfer(self, amount_naira, recipient_code, reason=None, reference=None):
        """
        Initiate a bank transfer to a recipient.

        Args:
            amount_naira: Amount in Naira
            recipient_code: Paystack recipient code
            reason: Transfer narration
            reference: Optional unique reference

        Returns:
            dict: {transfer_code, reference, status, ...} on success
            None on failure
        """
        amount_kobo = int(Decimal(str(amount_naira)) * 100)

        payload = {
            "source": "balance",
            "amount": amount_kobo,
            "recipient": recipient_code,
            "reason": reason or "GidiNest withdrawal",
        }
        if reference:
            payload["reference"] = reference

        try:
            resp = requests.post(
                f"{PAYSTACK_BASE_URL}/transfer",
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            data = resp.json()

            if data.get("status") is True:
                logger.info(f"Paystack transfer initiated: {data['data'].get('reference')}")
                return data["data"]
            else:
                logger.error(f"Paystack transfer failed: {data.get('message')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Paystack transfer request error: {e}")
            return None

    def resolve_account(self, account_number, bank_code):
        """
        Resolve a bank account number to get the account name.

        Returns:
            dict: {account_number, account_name} on success
            None on failure
        """
        try:
            resp = requests.get(
                f"{PAYSTACK_BASE_URL}/bank/resolve",
                params={"account_number": account_number, "bank_code": bank_code},
                headers=self.headers,
                timeout=30,
            )
            data = resp.json()

            if data.get("status") is True:
                return data["data"]
            else:
                logger.error(f"Paystack resolve failed: {data.get('message')}")
                return None
        except requests.RequestException as e:
            logger.error(f"Paystack resolve request error: {e}")
            return None

    def list_banks(self):
        """
        List all Nigerian banks supported by Paystack.

        Returns:
            list of dicts: [{name, code, ...}, ...]
        """
        try:
            resp = requests.get(
                f"{PAYSTACK_BASE_URL}/bank",
                params={"country": "nigeria"},
                headers=self.headers,
                timeout=30,
            )
            data = resp.json()

            if data.get("status") is True:
                return data["data"]
            return []
        except requests.RequestException as e:
            logger.error(f"Paystack list banks error: {e}")
            return []

    # ------------------------------------------------------------------
    # Webhook verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_webhook_signature(payload_body, signature):
        """
        Verify Paystack webhook HMAC-SHA512 signature.

        Args:
            payload_body: Raw request body (bytes)
            signature: x-paystack-signature header value

        Returns:
            bool: True if signature is valid
        """
        secret = settings.PAYSTACK_SECRET_KEY
        if not secret:
            logger.error("PAYSTACK_SECRET_KEY not set — cannot verify webhook")
            return False

        expected = hmac.new(
            secret.encode("utf-8"),
            payload_body,
            hashlib.sha512,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
