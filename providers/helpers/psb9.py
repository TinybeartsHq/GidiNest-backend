"""
9PSB (9 Payment Service Bank) API Client
Handles wallet operations, transfers, and account management for V2
"""

import requests
import json
import logging
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PSB9Client:
    """
    Client for 9 Payment Service Bank (9PSB) Wallet-as-a-Service API.

    Handles:
    - Authentication
    - Wallet opening/creation
    - Wallet operations (balance, transactions)
    - Transfers and withdrawals
    - Account tier upgrades
    """

    def __init__(self):
        """Initialize 9PSB client with credentials from settings"""
        self.username = getattr(settings, 'PSB9_USERNAME', None)
        self.password = getattr(settings, 'PSB9_PASSWORD', None)
        self.client_id = getattr(settings, 'PSB9_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'PSB9_CLIENT_SECRET', None)
        self.base_url = getattr(settings, 'PSB9_BASE_URL', 'http://102.216.128.75:9090')
        self.merchant_id = getattr(settings, 'PSB9_MERCHANT_ID', None)

        # Cache key for storing auth token
        self.token_cache_key = 'psb9_auth_token'
        self.token = None

        if not self.username or not self.password or not self.client_id or not self.client_secret:
            logger.warning("9PSB credentials not configured in settings")

    def _get_headers(self, authenticated=True):
        """
        Get HTTP headers for 9PSB API requests.

        Args:
            authenticated (bool): Whether to include authentication token

        Returns:
            dict: HTTP headers
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        if authenticated:
            token = self._get_auth_token()
            if token:
                headers['Authorization'] = f'Bearer {token}'

        return headers

    def _get_auth_token(self):
        """
        Get authentication token (from cache or by authenticating).
        Token is cached for 50 minutes (9PSB tokens last 1 hour).

        Returns:
            str: Bearer token or None if authentication fails
        """
        # Check cache first
        cached_token = cache.get(self.token_cache_key)
        if cached_token:
            return cached_token

        # Authenticate and cache token
        token = self.authenticate()
        if token:
            # Cache for 50 minutes (tokens last 1 hour, refresh before expiry)
            cache.set(self.token_cache_key, token, timeout=50*60)
            return token

        return None

    def authenticate(self):
        """
        Authenticate with 9PSB WAAS API and get bearer token.

        Endpoint: POST /bank9ja/api/v2/k1/authenticate

        Returns:
            str: Bearer token or None if authentication fails
        """
        if not self.username or not self.password or not self.client_id or not self.client_secret:
            logger.error("9PSB credentials missing")
            return None

        url = f"{self.base_url}/bank9ja/api/v2/k1/authenticate"

        payload = {
            "username": self.username,
            "password": self.password,
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }

        try:
            logger.info("Authenticating with 9PSB WAAS API")
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 9PSB returns token as 'accessToken' (not nested in 'data')
            if data.get('message') == 'successful' and data.get('accessToken'):
                token = data['accessToken']
                logger.info("9PSB authentication successful")
                return token
            # Fallback: try old format (data.token) for compatibility
            elif data.get('status') == 'success' and data.get('data', {}).get('token'):
                token = data['data']['token']
                logger.info("9PSB authentication successful")
                return token
            else:
                logger.error(f"9PSB authentication failed: {data}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB authentication request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"9PSB authentication response invalid JSON: {e}")
            return None

    def open_wallet(self, customer_data):
        """
        Open a new wallet for a customer.

        Endpoint: POST /waas/api/v1/open_wallet

        Args:
            customer_data (dict): Customer information
                Required fields:
                - firstName (str)
                - lastName (str)
                - otherNames (str): First name + middle name (9PSB shows lastName + otherNames in account name)
                - phoneNo (str): Phone number (not phoneNumber!)
                - email (str)
                - bvn (str): 11-digit BVN
                - gender (int): 1 for Male, 2 for Female
                - dateOfBirth (str): Format "dd/mm/yyyy" e.g. "21/09/1993" (NOT YYYY-MM-DD!)
                - address (str)
                - transactionTrackingRef (str): Unique transaction reference ID

        Returns:
            dict: API response with account details
                {
                    "status": "success",
                    "data": {
                        "accountNumber": "0123456789",
                        "accountName": "John Doe",
                        "customerId": "PSB9_CUST_123",
                        "walletId": "PSB9_WALLET_123"
                    }
                }
        """
        url = f"{self.base_url}/waas/api/v1/open_wallet"
        headers = self._get_headers(authenticated=True)

        # Add merchant ID to payload
        payload = {
            "merchantId": self.merchant_id,
            **customer_data
        }

        try:
            logger.info(f"Opening 9PSB wallet for {customer_data.get('email')}")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()

            # Check if wallet already exists (9PSB returns FAILED status but includes wallet data)
            if 'already exists' in data.get('message', '').lower():
                wallet_data = data.get('data', {})
                logger.info(f"9PSB wallet already exists, extracting details: {wallet_data.get('accountNumber')}")
                return {"status": "success", "data": wallet_data}

            # Check status case-insensitively (9PSB returns 'SUCCESS' not 'success')
            if data.get('status', '').upper() == 'SUCCESS':
                wallet_data = data.get('data', {})
                logger.info(f"9PSB wallet opened successfully: {wallet_data.get('accountNumber')}")
                return {"status": "success", "data": wallet_data}
            else:
                logger.error(f"9PSB wallet opening failed: {data}")
                return {"status": "error", "message": data.get('message', 'Unknown error'), "data": data}

        except requests.exceptions.HTTPError as e:
            error_message = f"9PSB API error: {e}"
            error_details = None
            try:
                error_data = response.json()
                error_message = error_data.get('message', error_message)
                error_details = error_data

                # Check if wallet already exists (9PSB returns HTTP error but includes wallet data)
                if 'already exists' in error_message.lower():
                    wallet_data = error_data.get('data', {})
                    logger.info(f"9PSB wallet already exists (HTTP error), extracting details: {wallet_data.get('accountNumber')}")
                    return {"status": "success", "data": wallet_data}

                logger.error(f"9PSB wallet opening HTTP error: {error_message}. Full response: {error_data}")
            except:
                logger.error(f"9PSB wallet opening HTTP error: {error_message}. Status: {response.status_code}")
            return {"status": "error", "message": error_message, "details": error_details}
        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB wallet opening request failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"9PSB wallet opening response invalid JSON: {e}")
            return {"status": "error", "message": "Invalid response from 9PSB"}

    def get_wallet_balance(self, account_number):
        """
        Get wallet balance for an account.

        Endpoint: POST /waas/api/v1/wallet/enquiry

        Args:
            account_number (str): 10-digit account number

        Returns:
            dict: API response with balance
                {
                    "status": "success",
                    "data": {
                        "accountNumber": "0123456789",
                        "accountName": "John Doe",
                        "balance": "50000.00",
                        "currency": "NGN"
                    }
                }
        """
        url = f"{self.base_url}/waas/api/v1/wallet_enquiry"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'success':
                return {"status": "success", "data": data.get('data')}
            else:
                logger.error(f"9PSB balance enquiry failed: {data}")
                return {"status": "error", "message": data.get('message', 'Unknown error')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB balance enquiry failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"9PSB balance response invalid JSON: {e}")
            return {"status": "error", "message": "Invalid response from 9PSB"}

    def get_transaction_history(self, account_number, start_date=None, end_date=None, page=1, limit=50):
        """
        Get transaction history for a wallet.

        Endpoint: POST /waas/api/v1/wallet/transactions

        Args:
            account_number (str): 10-digit account number
            start_date (str, optional): Start date in format "YYYY-MM-DD"
            end_date (str, optional): End date in format "YYYY-MM-DD"
            page (int): Page number (default: 1)
            limit (int): Results per page (default: 50)

        Returns:
            dict: API response with transaction list
        """
        url = f"{self.base_url}/waas/api/v1/wallet/transactions"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number,
            "page": page,
            "limit": limit
        }

        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'success':
                return {"status": "success", "data": data.get('data')}
            else:
                logger.error(f"9PSB transaction history failed: {data}")
                return {"status": "error", "message": data.get('message', 'Unknown error')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB transaction history failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"9PSB transaction response invalid JSON: {e}")
            return {"status": "error", "message": "Invalid response from 9PSB"}

    def initiate_transfer(self, from_account, to_account, to_bank_code, amount, narration, reference):
        """
        Initiate transfer/withdrawal from wallet to bank account.

        Endpoint: POST /waas/api/v1/wallet/transfer

        Args:
            from_account (str): Source account number (10 digits)
            to_account (str): Destination account number (10 digits)
            to_bank_code (str): CBN bank code (e.g., "044" for Access Bank)
            amount (float): Transfer amount in Naira
            narration (str): Transfer description
            reference (str): Unique transaction reference

        Returns:
            dict: API response with transfer status
        """
        url = f"{self.base_url}/waas/api/v1/wallet/transfer"
        headers = self._get_headers(authenticated=True)

        payload = {
            "fromAccount": from_account,
            "toAccount": to_account,
            "toBankCode": to_bank_code,
            "amount": float(amount),
            "narration": narration,
            "reference": reference
        }

        try:
            logger.info(f"Initiating 9PSB transfer: {from_account} -> {to_account}, amount: {amount}")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'success':
                logger.info(f"9PSB transfer successful: {reference}")
                return {"status": "success", "data": data.get('data')}
            else:
                logger.error(f"9PSB transfer failed: {data}")
                return {"status": "error", "message": data.get('message', 'Transfer failed')}

        except requests.exceptions.HTTPError as e:
            error_message = f"9PSB API error: {e}"
            try:
                error_data = response.json()
                error_message = error_data.get('message', error_message)
            except:
                pass
            logger.error(f"9PSB transfer HTTP error: {error_message}")
            return {"status": "error", "message": error_message}
        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB transfer request failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"9PSB transfer response invalid JSON: {e}")
            return {"status": "error", "message": "Invalid response from 9PSB"}

    def verify_account(self, account_number, bank_code):
        """
        Verify recipient bank account details.

        Endpoint: POST /waas/api/v1/verify_account

        Args:
            account_number (str): Account number to verify (10 digits)
            bank_code (str): CBN bank code (e.g., "044")

        Returns:
            dict: API response with account details
                {
                    "status": "success",
                    "data": {
                        "accountNumber": "0123456789",
                        "accountName": "John Doe",
                        "bankCode": "044",
                        "bankName": "Access Bank"
                    }
                }
        """
        url = f"{self.base_url}/waas/api/v1/verify_account"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number,
            "bankCode": bank_code
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'success':
                return {"status": "success", "data": data.get('data')}
            else:
                logger.error(f"9PSB account verification failed: {data}")
                return {"status": "error", "message": data.get('message', 'Verification failed')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB account verification failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"9PSB verification response invalid JSON: {e}")
            return {"status": "error", "message": "Invalid response from 9PSB"}

    def upgrade_account_tier(self, account_number, tier, kyc_data):
        """
        Upgrade account to higher tier (Tier 2 or Tier 3).

        Endpoint: POST /waas/api/v1/upgrade_account

        Args:
            account_number (str): Account number to upgrade
            tier (int): Target tier (2 or 3)
            kyc_data (dict): KYC information
                For Tier 2 (BVN):
                - bvn (str): 11-digit BVN
                For Tier 3 (NIN):
                - nin (str): 11-digit NIN

        Returns:
            dict: API response with upgrade status
        """
        url = f"{self.base_url}/waas/api/v1/upgrade_account"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number,
            "tier": tier,
            **kyc_data
        }

        try:
            logger.info(f"Upgrading 9PSB account {account_number} to Tier {tier}")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'success':
                logger.info(f"9PSB account upgrade successful: {account_number} -> Tier {tier}")
                return {"status": "success", "data": data.get('data')}
            else:
                logger.error(f"9PSB account upgrade failed: {data}")
                return {"status": "error", "message": data.get('message', 'Upgrade failed')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB account upgrade failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"9PSB upgrade response invalid JSON: {e}")
            return {"status": "error", "message": "Invalid response from 9PSB"}

    def get_wallet_status(self, account_number):
        """
        Get wallet status and information.

        Endpoint: POST /waas/api/v1/wallet/status

        Args:
            account_number (str): 10-digit account number

        Returns:
            dict: API response with wallet status
        """
        url = f"{self.base_url}/waas/api/v1/wallet/status"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status') == 'success':
                return {"status": "success", "data": data.get('data')}
            else:
                logger.error(f"9PSB wallet status check failed: {data}")
                return {"status": "error", "message": data.get('message', 'Unknown error')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB wallet status check failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"9PSB status response invalid JSON: {e}")
            return {"status": "error", "message": "Invalid response from 9PSB"}

    def debit_wallet(self, account_number, amount, transaction_id, narration="Debit"):
        """
        Test Case 4: Debit Wallet
        """
        url = f"{self.base_url}/waas/api/v1/debit/transfer"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number,
            "amount": amount,
            "transactionId": transaction_id,
            "narration": narration
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', {})}
            else:
                return {"status": "error", "message": data.get('message', 'Debit failed'), "data": data}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB debit wallet failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def credit_wallet(self, account_number, amount, transaction_id, narration="Credit"):
        """
        Test Case 5: Credit Wallet
        """
        url = f"{self.base_url}/waas/api/v1/credit/transfer"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number,
            "amount": amount,
            "transactionId": transaction_id,
            "narration": narration
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', {})}
            else:
                return {"status": "error", "message": data.get('message', 'Credit failed'), "data": data}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB credit wallet failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def get_banks(self):
        """
        Test Case 14: Get Banks
        """
        url = f"{self.base_url}/waas/api/v1/get_banks"
        headers = self._get_headers(authenticated=True)

        try:
            response = requests.post(url, json={}, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', [])}
            else:
                return {"status": "error", "message": data.get('message', 'Failed to get banks')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB get banks failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def other_banks_enquiry(self, account_number, bank_code):
        """
        Test Case 6: Other Banks Account Enquiry
        """
        url = f"{self.base_url}/waas/api/v1/other_banks_enquiry"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number,
            "bankCode": bank_code
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', {})}
            else:
                return {"status": "error", "message": data.get('message', 'Account enquiry failed')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB account enquiry failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def other_banks_transfer(self, sender_account_number, receiver_account_number, bank_code, amount, transaction_id, narration="Transfer"):
        """
        Test Case 7: Other Banks Transfer
        """
        url = f"{self.base_url}/waas/api/v1/wallet_other_banks"
        headers = self._get_headers(authenticated=True)

        payload = {
            "senderAccountNumber": sender_account_number,
            "receiverAccountNumber": receiver_account_number,
            "bankCode": bank_code,
            "amount": amount,
            "transactionId": transaction_id,
            "narration": narration
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', {})}
            else:
                return {"status": "error", "message": data.get('message', 'Transfer failed'), "data": data}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB transfer failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def get_wallet_transactions(self, account_number, start_date=None, end_date=None):
        """
        Test Case 8: Wallet Transaction History
        """
        url = f"{self.base_url}/waas/api/v1/wallet_transactions"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number
        }

        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', [])}
            else:
                return {"status": "error", "message": data.get('message', 'Failed to get transactions')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB transaction history failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def transaction_requery(self, transaction_id):
        """
        Test Case 11: Wallet Transaction Requery
        """
        url = f"{self.base_url}/waas/api/v1/wallet_requery"
        headers = self._get_headers(authenticated=True)

        payload = {
            "transactionId": transaction_id
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', {})}
            else:
                return {"status": "error", "message": data.get('message', 'Transaction not found')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB transaction requery failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def get_wallet_status(self, account_number):
        """
        Test Case 9: Wallet Status
        """
        url = f"{self.base_url}/waas/api/v1/wallet_status"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', {})}
            else:
                return {"status": "error", "message": data.get('message', 'Failed to get wallet status')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB wallet status failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}

    def change_wallet_status(self, account_number, status):
        """
        Test Case 10: Change Wallet Status
        """
        url = f"{self.base_url}/waas/api/v1/change_wallet_status"
        headers = self._get_headers(authenticated=True)

        payload = {
            "accountNumber": account_number,
            "status": status
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('status', '').upper() == 'SUCCESS':
                return {"status": "success", "data": data.get('data', {})}
            else:
                return {"status": "error", "message": data.get('message', 'Failed to change status')}

        except requests.exceptions.RequestException as e:
            logger.error(f"9PSB change status failed: {e}")
            return {"status": "error", "message": f"Network error: {str(e)}"}


# Create a singleton instance for easy imports
psb9_client = PSB9Client()
