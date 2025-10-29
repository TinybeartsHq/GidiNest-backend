import requests
import json
from typing import Optional, Dict, Any
from django.conf import settings

from core.helpers.messaging import BVN_VALIDATION_FAILED


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
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
           Private helper to handle API requests and general error handling.
        """
        url = f"{self.base_url}/{endpoint}"
        payload = json.dumps(data) if data else None
        try:
            response = requests.request(
                method, url, headers=self.headers, data=payload, params=params, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            if(response.status_code == 401):
                return {"success": False, "message":BVN_VALIDATION_FAILED }
            elif(response.status_code == 404):          

                return {"success": False, "message": BVN_VALIDATION_FAILED}
            elif(response.status_code == 500):
                return {"success": False, "message": BVN_VALIDATION_FAILED}
            return {"success": False, "message": "An error occurred please try again later", "data": response.json()}
        
        except requests.exceptions.RequestException as req_err:
            print(f"Request error: {req_err}")
            return {"success": False, "message": f"Network error: {req_err}"}
        except json.JSONDecodeError as json_err:
            print(f"JSON decode error: {json_err} - Raw response: {response.text}")
            return {"success": False, "message": "Failed to parse API response."}
        
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

        print(payload)
 
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
        # Step 1: Create the customer
        customer_response = self.create_customer(**customer_data)
        if not customer_response.get("success"):
            return customer_response

        customer_id = customer_response["data"]["id"]
        result = {"customer": customer_response["data"]}

        # Step 2: Upgrade KYC if BVN is provided
        if bvn:
            kyc_response = self.upgrade_kyc(customer_id=customer_id, bvn=bvn)
            if not kyc_response.get("success"):
                return {"success": False, "message": "KYC upgrade failed.", "details": kyc_response}
            result["kyc"] = kyc_response["data"]

        # Step 3: Create a wallet if data is provided
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