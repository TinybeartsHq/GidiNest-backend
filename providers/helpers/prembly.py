import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def verify_bvn(bvn: str):
    """
    Handles BVN verification using Prembly's Identitypass API.

        Args:
            bvn (str): The 11-digit Bank Verification Number (BVN) to verify.

        Returns:
            dict: The JSON response from the Prembly API.
                Returns an error dictionary if the request fails or API key is missing.
    """


    PREMBLY_API_KEY = settings.PREMBLY_API_KEY
    PREMBLY_APP_ID = getattr(settings, 'PREMBLY_APP_ID', None)

    # Correct Prembly API endpoint (verified from docs)
    API_URL = "https://api.prembly.com/verification/bvn"

    if not PREMBLY_API_KEY:
        logger.error("PREMBLY_API_KEY not configured")
        return {"status": "error", "message": "Prembly API Key is missing or not configured."}

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'x-api-key': PREMBLY_API_KEY,
    }

    # Add APP ID if configured
    if PREMBLY_APP_ID:
        headers['app-id'] = PREMBLY_APP_ID

    # Prembly BVN payload
    data = {
        'number': bvn
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()

        response_data = response.json()

        # Check if Prembly returned an error (e.g., insufficient balance)
        if response_data.get('status') == False or response_data.get('verification', {}).get('status') == 'FAILED':
            error_detail = response_data.get('detail', 'Verification failed')
            logger.warning(f"Prembly BVN verification failed: {error_detail}")
            return {"status": "error", "message": error_detail, "details": response_data}

        return {"status":"success","data":response_data}

    except requests.exceptions.HTTPError as http_err:
        status_code = response.status_code if hasattr(response, 'status_code') else 'N/A'
        logger.error(f"Prembly BVN HTTP error: {http_err} - Status: {status_code}")
        return {"status": "error", "message": "BVN verification service error. Please try again."}
    except requests.exceptions.ConnectionError:
        logger.error("Prembly BVN connection error")
        return {"status": "error", "message": "Network error: Could not connect to verification service."}
    except requests.exceptions.Timeout:
        logger.error("Prembly BVN request timed out")
        return {"status": "error", "message": "Verification service request timed out."}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Prembly BVN unexpected error: {req_err}")
        return {"status": "error", "message": "An unexpected error during verification."}
    except json.JSONDecodeError as json_err:
        logger.error(f"Prembly BVN JSON decode error: {json_err}")
        return {"status": "error", "message": "Failed to parse verification response."}


def verify_nin(nin: str, first_name: str = None, last_name: str = None, dob: str = None):
    """
    Handles NIN verification using Prembly's API.

    Args:
        nin (str): The 11-digit National Identification Number (NIN) to verify.
        first_name (str, optional): First name for matching (if required by API).
        last_name (str, optional): Last name for matching (if required by API).
        dob (str, optional): Date of birth for matching (if required by API).

    Returns:
        dict: The JSON response from the Prembly API.
            Returns an error dictionary if the request fails or API key is missing.
    """

    PREMBLY_API_KEY = settings.PREMBLY_API_KEY
    PREMBLY_APP_ID = getattr(settings, 'PREMBLY_APP_ID', None)

    API_URL = "https://api.prembly.com/verification/vnin"

    if not PREMBLY_API_KEY:
        logger.error("PREMBLY_API_KEY not configured")
        return {"status": "error", "message": "Prembly API Key is missing or not configured."}

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'x-api-key': PREMBLY_API_KEY,
    }

    # Add APP ID if configured
    if PREMBLY_APP_ID:
        headers['app-id'] = PREMBLY_APP_ID

    # Build payload - NIN uses 'number_nin' field (per Prembly docs)
    data = {
        'number_nin': nin
    }

    # Add optional fields if provided
    if first_name:
        data['firstname'] = first_name
    if last_name:
        data['lastname'] = last_name
    if dob:
        data['dob'] = dob

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()

        response_data = response.json()

        # Check if Prembly returned an error (e.g., insufficient balance)
        if response_data.get('status') == False or response_data.get('verification', {}).get('status') == 'FAILED':
            error_detail = response_data.get('detail', 'Verification failed')
            logger.warning(f"Prembly NIN verification failed: {error_detail}")
            return {"status": "error", "message": error_detail, "details": response_data}

        return {"status": "success", "data": response_data}

    except requests.exceptions.HTTPError as http_err:
        status_code = response.status_code if hasattr(response, 'status_code') else 'N/A'
        logger.error(f"Prembly NIN HTTP error: {http_err} - Status: {status_code}")
        return {"status": "error", "message": "NIN verification service error. Please try again."}
    except requests.exceptions.ConnectionError:
        logger.error("Prembly NIN connection error")
        return {"status": "error", "message": "Network error: Could not connect to verification service."}
    except requests.exceptions.Timeout:
        logger.error("Prembly NIN request timed out")
        return {"status": "error", "message": "Verification service request timed out."}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Prembly NIN unexpected error: {req_err}")
        return {"status": "error", "message": "An unexpected error during verification."}
    except json.JSONDecodeError as json_err:
        logger.error(f"Prembly NIN JSON decode error: {json_err}")
        return {"status": "error", "message": "Failed to parse verification response."}
