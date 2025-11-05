import requests
import json
from typing import Optional, Dict, Any
from django.conf import settings

from core.helpers.messaging import BVN_VALIDATION_FAILED
from providers.models import ProviderRequestLog


class EmbedlyClient:
    """
    A client for the Embedly WAAS API, designed to handle multi-step
    processes like customer onboarding and wallet creation.
    """
    def __init__(self):
        """
        Initializes the EmbedlyClient with an API key and organization ID.

        Args:
            api_key (str): The x-api-key for authentication.
            organization_id (str): The ID of the organization.
            base_url (str): The base URL of the Embedly API.
        """

        self.api_key = settings.EMBEDLY_API_KEY_PRODUCTION
        self.organization_id = settings.EMBEDLY_ORGANIZATION_ID_PRODUCTION
        self.base_url = "https://waas-prod.embedly.ng/api/v1"
        self.payout_base_url = "https://payout-prod.embedly.ng/api"  # Payout API uses different base URL
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key
        }
    
    def _log_to_db(
        self,
        endpoint: str,
        method: str,
        request_payload: dict,
        response: dict,
        status_code: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Persist API interaction details in DB."""
        try:
            # Safely check success status
            success = False
            if response and isinstance(response, dict):
                success = response.get("success", False)

            ProviderRequestLog.objects.create(
                provider_name="Embedly",
                http_method=method,
                endpoint=endpoint,
                request_payload=request_payload or {},
                response_body=response or {},
                response_status=status_code,
                success=success,
                error_message=error,
            )
        except Exception as e:
            # Fallback logging in case DB logging fails
            print(f"[DB LOGGING ERROR] Failed to log Embedly request: {e}")

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
           Private helper to handle API requests and general error handling.
        """
        # Use payout_base_url for Payout endpoints, otherwise use regular base_url
        if endpoint.startswith("Payout/"):
            url = f"{self.payout_base_url}/{endpoint}"
        else:
            url = f"{self.base_url}/{endpoint}"

        payload = json.dumps(data) if data else None
        response = None

        try:
            response = requests.request(
                method, url, headers=self.headers, data=payload, params=params, timeout=30
            )
            response.raise_for_status()

            result = response.json()

            self._log_to_db(endpoint, method, data, result, response.status_code)
            return {"success": True, "data": result['data']}

        except requests.exceptions.HTTPError as http_err:
            # Try to parse error response
            error_data = None
            status_code = response.status_code if response else None

            try:
                if response is not None:
                    error_data = response.json()
            except Exception as json_error:
                if response is not None:
                    error_data = {"raw_response": response.text, "json_error": str(json_error)}

            self._log_to_db(endpoint, method, data, error_data, status_code, str(http_err))

            if status_code == 401:
                return {"success": False, "message": BVN_VALIDATION_FAILED, "code": "401"}
            elif status_code == 404:
                return {"success": False, "message": BVN_VALIDATION_FAILED, "code": "404"}
            elif status_code == 500:
                return {"success": False, "message": BVN_VALIDATION_FAILED, "code": "500"}
            elif status_code == 400:
                # Bad request - return the actual error message from Embedly
                error_msg = "Invalid request"
                if error_data and isinstance(error_data, dict):
                    error_msg = error_data.get('message', error_data.get('error', error_msg))
                return {"success": False, "message": error_msg, "code": "-904", "data": error_data}

            # For other errors, try to get meaningful message
            error_msg = "An error occurred please try again later"
            if error_data and isinstance(error_data, dict):
                error_msg = error_data.get('message', error_data.get('error', error_msg))

            return {"success": False, "message": error_msg, "data": error_data}

        except requests.exceptions.RequestException as req_err:
            self._log_to_db(endpoint, method, data, None, None, str(req_err))
            return {"success": False, "message": f"Network error: {req_err}"}

        except json.JSONDecodeError as json_err:
            raw_text = response.text if response else "No response"
            status_code = response.status_code if response else None

            # Log the parsing error with status code
            error_detail = {
                "raw_response": raw_text,
                "json_error": str(json_err),
                "status_code": status_code,
                "url": url
            }
            self._log_to_db(endpoint, method, data, error_detail, status_code, str(json_err))

            # Return more detailed error
            return {
                "success": False,
                "message": f"Failed to parse API response. Status: {status_code}, Response: {raw_text[:100] if raw_text else 'empty'}",
                "data": error_detail
            }
        
    def create_customer(self, payload: dict = None) -> Dict[str, Any]:
        """
        Creates a new customer.
        
        Args:
            first_name (str): The customer's first name.
            last_name (str): The customer's last name.
            email_address (Optional[str]): The customer's email.
            mobile_number (Optional[str]): The customer's mobile number.
            **kwargs: Additional optional customer data (e.g., dob, address, city, etc.).

        Returns:
            Dict[str, Any]: The API response.
        """
        endpoint = "customers/add"
   
        payload["customerTypeId"] = settings.EMBEDLY_CUSTOMER_TYPE_ID_INDIVIDUAL
        payload["countryId"] = settings.EMBEDLY_COUNTRY_ID_NIGERIA
        payload["alias"] =  payload['firstName']

        return self._make_request("POST", endpoint, data=payload)

    def upgrade_kyc(self, customer_id: str, bvn: str) -> Dict[str, Any]:
        """
        Upgrades a customer's KYC using their BVN.

        Args:
            customer_id (str): The unique ID of the customer.
            bvn (str): The 11-digit Bank Verification Number.

        Returns:
            Dict[str, Any]: The API response.
        """
        endpoint = "customers/kyc/premium-kyc"
        payload = {"customerId": customer_id, "bvn": bvn}
        res =  self._make_request("POST", endpoint, data=payload)
        return res

    def upgrade_kyc_nin(self, customer_id: str, nin: str, firstname: str, lastname: str, dob: str) -> Dict[str, Any]:
        """
        Upgrades a customer's KYC using their NIN.

        Args:
            customer_id (str): The unique ID of the customer.
            nin (str): The 11-digit National Identification Number.
            firstname (str): The customer's first name as stated against their NIN.
            lastname (str): The customer's last name as stated against their NIN.
            dob (str): The customer's date of birth (format: "1999-10-27T09").

        Returns:
            Dict[str, Any]: The API response.
        """
        endpoint = "customers/kyc/customer/nin"
        params = {
            "customerId": customer_id,
            "nin": nin,
            "verify": "1"
        }
        payload = {
            "firstname": firstname,
            "lastname": lastname,
            "dob": dob
        }
        res = self._make_request("POST", endpoint, data=payload, params=params)
        return res

    def create_wallet(self, customer_id: str, name: str, phone: str) -> Dict[str, Any]:
        """
        Creates a new wallet for a customer.
        
        Args:
            customer_id (str): The unique ID of the customer.
            wallet_group_id (str): The ID of the wallet group.
            customer_type_id (str): The ID for the customer type.
            currency_id (str): The ID of the currency.
            **kwargs: Additional optional wallet data.

        Returns:
            Dict[str, Any]: The API response.
        """
        endpoint = "wallets/add"
        payload = {
            "walletGroupId": "3fa85f14-5717-4562-b3fc-2c963f66afa6",
            "customerId": customer_id,
            "availableBalance": 0,
            "ledgerBalance": 0,
            "currencyId": "45852f0c-84fa-410c-b66c-1ffec56e5cd8",
            "isInternal": False,
            "isDefault": True,
            "name": name,
            "overdraft": 0,
            "customerTypeId": settings.EMBEDLY_CUSTOMER_TYPE_ID_INDIVIDUAL,
            "mobNum":phone
        }
        return self._make_request("POST", endpoint, data=payload)

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieves customer information from Embedly, including KYC status.

        Args:
            customer_id (str): The unique ID of the customer.

        Returns:
            Dict[str, Any]: The API response with customer details.
        """
        endpoint = f"customers/{customer_id}"
        return self._make_request("GET", endpoint)

    def get_wallet_info(self, account_number: str) -> Dict[str, Any]:
        """
        Retrieves wallet information using the virtual account number.

        Args:
            account_number (str): The virtual account number.

        Returns:
            Dict[str, Any]: The API response.
        """
        endpoint = f"wallets/get/wallet/account/{account_number}"
        return self._make_request("GET", endpoint)

    def get_banks(self) -> Dict[str, Any]:
        """
        Retrieves list of banks available for processing transfers.

        Returns:
            Dict[str, Any]: The API response with list of banks.
            Example success response:
            {
                "success": True,
                "data": [
                    {
                        "bankCode": "000010",
                        "bankName": "Sterling Bank",
                        ...
                    }
                ]
            }
        """
        endpoint = "Payout/banks"
        return self._make_request("GET", endpoint)

    def resolve_bank_account(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """
        Validates external bank account and retrieves account name.
        Bank Account Name Enquiry endpoint.

        Args:
            account_number (str): The bank account number to validate (10 digits).
            bank_code (str): The bank code (e.g., "000010" for Sterling Bank).

        Returns:
            Dict[str, Any]: The API response with account details.
            Example success response:
            {
                "success": True,
                "data": {
                    "accountNumber": "1111111111",
                    "accountName": "JOHN DOE",
                    "bankCode": "000010"
                }
            }
        """
        endpoint = "Payout/name-enquiry"
        payload = {
            "accountNumber": account_number,
            "bankCode": bank_code
        }
        return self._make_request("POST", endpoint, data=payload)

    def initiate_bank_transfer(
        self,
        destination_bank_code: str,
        destination_account_number: str,
        destination_account_name: str,
        source_account_number: str,
        source_account_name: str,
        amount: int,
        currency_id: str,
        remarks: str = "Withdrawal",
        webhook_url: Optional[str] = None,
        customer_transaction_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiates an inter-bank transfer (withdrawal/payout).

        Args:
            destination_bank_code (str): Bank code of recipient (e.g., "000010").
            destination_account_number (str): Recipient account number (10 digits).
            destination_account_name (str): Recipient account name.
            source_account_number (str): Source wallet account number.
            source_account_name (str): Source account name.
            amount (int): Amount in kobo/cents (e.g., 100000 = NGN 1,000).
            currency_id (str): Currency UUID.
            remarks (str): Transaction narration/description.
            webhook_url (str, optional): URL for transaction status webhook.
            customer_transaction_reference (str, optional): Your reference.

        Returns:
            Dict[str, Any]: The API response with transaction reference.
            Example success response:
            {
                "success": True,
                "data": {
                    "transactionRef": "3212-1234-5678-9101",
                    ...
                }
            }
        """
        endpoint = "Payout/inter-bank-transfer"
        payload = {
            "destinationBankCode": destination_bank_code,
            "destinationAccountNumber": destination_account_number,
            "destinationAccountName": destination_account_name,
            "sourceAccountNumber": source_account_number,
            "sourceAccountName": source_account_name,
            "amount": amount,
            "currencyId": currency_id,
            "remarks": remarks
        }

        if webhook_url:
            payload["webhookUrl"] = webhook_url

        if customer_transaction_reference:
            payload["customerTransactionReference"] = customer_transaction_reference

        return self._make_request("POST", endpoint, data=payload)

    def get_transfer_status(self, transaction_ref: str) -> Dict[str, Any]:
        """
        Re-queries the status of a payout transaction.

        Args:
            transaction_ref (str): The unique transaction reference (e.g., "3212-1234-5678-9101").

        Returns:
            Dict[str, Any]: The API response with transaction status.
        """
        endpoint = f"Payout/status/{transaction_ref}"
        return self._make_request("GET", endpoint)

    def get_wallet_history(
        self,
        wallet_id: str,
        from_date: str,
        to_date: str,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Retrieves transaction history for a specific wallet.

        Args:
            wallet_id (str): Unique identifier for the wallet (UUID).
            from_date (str): Start date/time in ISO format (e.g., "2025-01-01T00:00:00Z").
            to_date (str): End date/time in ISO format (e.g., "2025-01-31T23:59:59Z").
            page (int): Page number (default: 1).
            page_size (int): Number of records per page (default: 50).

        Returns:
            Dict[str, Any]: The API response with transaction history.
            Example success response:
            {
                "success": True,
                "data": {
                    "transactions": [...],
                    "totalCount": 100,
                    "page": 1,
                    "pageSize": 50
                }
            }
        """
        endpoint = "wallets/history"
        payload = {
            "walletId": wallet_id,
            "From": from_date,
            "To": to_date,
            "Page": page,
            "PageSize": page_size
        }
        return self._make_request("POST", endpoint, data=payload)

    def register_and_onboard_customer(
            self, customer_data: Dict[str, Any], bvn: Optional[str] = None, wallet_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
            Performs a full customer onboarding flow: create customer, upgrade KYC (if BVN is provided),
            and create a default wallet (if wallet data is provided).

            Args:
                customer_data (Dict[str, Any]): A dictionary with customer details.
                bvn (Optional[str]): The customer's BVN for KYC upgrade.
                wallet_data (Optional[Dict[str, Any]]): A dictionary with wallet details.

            Returns:
                Dict[str, Any]: The final response from the onboarding process.
        """

        customer_response = self.create_customer(**customer_data)
        if not customer_response.get("success"):
            return customer_response

        customer_id = customer_response["data"]["id"]
        result = {"customer": customer_response["data"]}


        if bvn:
            kyc_response = self.upgrade_kyc(customer_id=customer_id, bvn=bvn)
            if not kyc_response.get("success"):
                return {"success": False, "message": "KYC upgrade failed.", "details": kyc_response}
            result["kyc"] = kyc_response["data"]


        if wallet_data:
            wallet_response = self.create_wallet(
                customer_id=customer_id,
                wallet_group_id=wallet_data.get("walletGroupId"),
                customer_type_id=wallet_data.get("customerTypeId"),
                currency_id=wallet_data.get("currencyId"),
                mobNum=customer_data.get("mobileNumber")
            )
            if not wallet_response.get("success"):
                return {"success": False, "message": "Wallet creation failed.", "details": wallet_response}
            result["wallet"] = wallet_response["data"]

        return {"success": True, "message": "Customer onboarded successfully.", "data": result}