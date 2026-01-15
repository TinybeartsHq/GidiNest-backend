#!/bin/bash

# Test script for 9PSB WAAS endpoints
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2MDY5NDY2LCJpYXQiOjE3NjYwNjU4NjYsImp0aSI6IjRiZTNhMGYwNTU1YzQxNjM4MjUxZDBlMmNmZjBiOGRmIiwidXNlcl9pZCI6ImU0M2YzMjExLTYzM2UtNDJjZi1hOGVkLWFmODRiNzc5ZjQ1ZiJ9.idgDlS2j6S4jRF4cs9K8XuTozIfVT7cR_KSDQWnu3js"
BASE_URL="https://app.gidinest.com/api/v2/wallet/9psb"

echo "=== Test Case 14: Get Banks ==="
curl -s -X GET "$BASE_URL/banks" -H "Authorization: Bearer $TOKEN" | head -200

echo -e "\n\n=== Test Case 3: Wallet Enquiry ==="
curl -s -X GET "$BASE_URL/enquiry" -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Test Case 9: Wallet Status ==="
curl -s -X GET "$BASE_URL/status" -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== Test Case 4: Debit Wallet (Insufficient Balance Expected) ==="
curl -s -X POST "$BASE_URL/debit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "narration": "Test debit for UAT"}'

echo -e "\n\n=== Test Case 11: Transaction Requery ==="
curl -s -X POST "$BASE_URL/transactions/requery" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"transaction_id": "TEST_UAT_123"}'

echo -e "\n\n=== Test Case 6: Other Banks Enquiry ==="
curl -s -X POST "$BASE_URL/banks/enquiry" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_number": "0690000031", "bank_code": "035"}'

echo -e "\n\n=== Test Case 7: Other Banks Transfer (Insufficient Balance Expected) ==="
curl -s -X POST "$BASE_URL/transfer/banks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 500, "account_number": "0690000031", "bank_code": "035", "account_name": "Test User", "narration": "Test transfer for UAT"}'

echo -e "\n\n=== Test Case 8: Transaction History ==="
curl -s -X GET "$BASE_URL/transactions?start_date=2025-12-01&end_date=2025-12-18" \
  -H "Authorization: Bearer $TOKEN"
