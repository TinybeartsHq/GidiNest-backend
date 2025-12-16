import requests
import os
import json
from django.conf import settings

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
        print("Error: PREMBLY_API_KEY environment variable not set.")
        return {"status": "error", "message": "Prembly API Key is missing or not configured. Please set the PREMBLY_API_KEY environment variable."}

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',  # Prembly uses JSON, not form-urlencoded
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
        # Use json parameter for JSON content-type
        response = requests.post(API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()

        response_data = response.json()
        print(f"DEBUG - Prembly BVN API Response: {response_data}")

        # Check if Prembly returned an error (e.g., insufficient balance)
        if response_data.get('status') == False or response_data.get('verification', {}).get('status') == 'FAILED':
            error_detail = response_data.get('detail', 'Verification failed')
            print(f"Prembly BVN verification failed: {error_detail}")
            return {"status": "error", "message": error_detail, "details": response_data}

        return {"status":"success","data":response_data}

    except requests.exceptions.HTTPError as http_err:
        status_code = response.status_code if hasattr(response, 'status_code') else 'N/A'
        response_text = response.text if hasattr(response, 'text') else 'N/A'
        print(f"HTTP error occurred: {http_err} - Status: {status_code} - Response: {response_text}")
        return {"status": "error", "message": f"API error: {http_err}", "details": response_text}
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        return {"status": "error", "message": f"Network error: Could not connect to Prembly."}
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return {"status": "error", "message": f"Prembly API request timed out."}
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
        return {"status": "error", "message": f"An unexpected error during API request."}
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error: {json_err} - Response text: {response.text}")
        return {"status": "error", "message": f"Failed to parse Prembly response.", "raw_response": response.text}


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
        print("Error: PREMBLY_API_KEY environment variable not set.")
        return {"status": "error", "message": "Prembly API Key is missing or not configured. Please set the PREMBLY_API_KEY environment variable."}

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
        print(f"DEBUG - Prembly NIN API Response: {response_data}")

        # Check if Prembly returned an error (e.g., insufficient balance)
        if response_data.get('status') == False or response_data.get('verification', {}).get('status') == 'FAILED':
            error_detail = response_data.get('detail', 'Verification failed')
            print(f"Prembly NIN verification failed: {error_detail}")
            return {"status": "error", "message": error_detail, "details": response_data}

        return {"status": "success", "data": response_data}

    except requests.exceptions.HTTPError as http_err:
        status_code = response.status_code if hasattr(response, 'status_code') else 'N/A'
        response_text = response.text if hasattr(response, 'text') else 'N/A'
        print(f"HTTP error occurred: {http_err} - Status: {status_code} - Response: {response_text}")
        return {"status": "error", "message": f"API error: {http_err}", "details": response_text}
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        return {"status": "error", "message": f"Network error: Could not connect to Prembly."}
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return {"status": "error", "message": f"Prembly API request timed out."}
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred: {req_err}")
        return {"status": "error", "message": f"An unexpected error during API request."}
    except json.JSONDecodeError as json_err:
        print(f"JSON decode error: {json_err} - Response text: {response.text}")
        return {"status": "error", "message": f"Failed to parse Prembly response.", "raw_response": response.text}