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
    
    API_URL = "https://api.prembly.com/identitypass/verification/bvn"

    if not PREMBLY_API_KEY:
        print("Error: PREMBLY_API_KEY environment variable not set.")
        return {"status": "error", "message": "Prembly API Key is missing or not configured. Please set the PREMBLY_API_KEY environment variable."}

    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'x-api-key': PREMBLY_API_KEY,
    }

    data = {
        'number': bvn
    }

    try:
        response = requests.post(API_URL, headers=headers, data=data, timeout=60) # Added timeout
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        return {"status":"success","data":response.json()}

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