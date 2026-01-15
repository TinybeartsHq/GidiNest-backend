#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2MDY5NDY2LCJpYXQiOjE3NjYwNjU4NjYsImp0aSI6IjRiZTNhMGYwNTU1YzQxNjM4MjUxZDBlMmNmZjBiOGRmIiwidXNlcl9pZCI6ImU0M2YzMjExLTYzM2UtNDJjZi1hOGVkLWFmODRiNzc5ZjQ1ZiJ9.idgDlS2j6S4jRF4cs9K8XuTozIfVT7cR_KSDQWnu3js"
BASE_URL="https://app.gidinest.com/api/v2/wallet/9psb"

echo "=== Test Case 5: Credit Wallet (Admin Only) ==="
curl -s -X POST "$BASE_URL/credit" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_number": "1100072011", "amount": 1000, "narration": "Test credit for UAT"}'

echo -e "\n\n=== Test Case 10: Change Wallet Status (Admin Only) ==="
curl -s -X POST "$BASE_URL/status/change" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"account_number": "1100072011", "status": "active"}'
