# Payment Link API Response Format

## Public Payment Link View
`GET /api/v2/wallet/payment-links/{token}/`

This endpoint is accessible to anyone with the token (no authentication required).

### Response Format:

```json
{
  "status": true,
  "message": "Success",
  "data": {
    "token": "abc123xyz456...",
    "link_type": "savings_goal",

    // Goal Information (if savings_goal type)
    "savings_goal_name": "Baby's Education Fund",
    "savings_goal_target": "100000.00",
    "savings_goal_current": "25000.00",
    "savings_goal_description": "Saving for my baby's future education",

    // Event Information (if event type)
    "event_name": "Baby Shower - March 2025",
    "event_date": "2025-03-15",
    "event_description": "Help us celebrate our baby!",

    // Link Settings
    "target_amount": "100000.00",
    "allow_custom_amount": true,
    "fixed_amount": null,
    "show_contributors": "public",
    "custom_message": "Thank you for your contribution!",
    "description": "Help fund my baby's education",

    // Progress & Status
    "total_raised": "25000.00",
    "contributor_count": 5,
    "target_reached": false,
    "progress_percentage": 25.0,
    "is_expired": false,
    "can_accept_payments": true,

    // BANK DETAILS - For Contributors to Make Payment
    "bank_details": {
      "bank_name": "Wema Bank",
      "bank_code": "035",
      "account_number": "1234567890",
      "account_name": "John Doe",
      "currency": "NGN"
    },

    // PAYMENT REFERENCE - MUST be used when making payment
    "payment_reference": "PL-abc123xyz456-1699999999",

    // Recent Contributors (based on privacy settings)
    "recent_contributors": [
      {
        "name": "Jane Smith",
        "amount": "10000.00",
        "message": "Congratulations!",
        "created_at": "2025-11-13T10:30:00Z"
      },
      {
        "name": "Mike Johnson",
        "amount": "5000.00",
        "message": "Best wishes!",
        "created_at": "2025-11-13T09:15:00Z"
      }
    ]
  }
}
```

## Key Fields for Frontend:

### For Display:
- `savings_goal_name` / `event_name` - Title
- `description` - Subtitle/description
- `progress_percentage` - Progress bar (0-100)
- `total_raised` - Amount raised so far
- `target_amount` - Goal target
- `contributor_count` - Number of people who contributed
- `recent_contributors` - List to display

### For Payment Instructions:
- `bank_details.bank_name` - Display: "Bank: Wema Bank"
- `bank_details.account_number` - Display: "Account Number: 1234567890"
- `bank_details.account_name` - Display: "Account Name: John Doe"
- `payment_reference` - **CRITICAL**: Display with copy button

### For Validation:
- `can_accept_payments` - Check before showing payment details
- `is_expired` - Show "This link has expired" if true

## How Contributors Use the Link:

1. Visit: `https://app.gidinest.com/pay/{token}`
2. See goal/event details and progress
3. Copy the **payment_reference** (very important!)
4. Transfer money to the account details shown
5. Use the copied reference as payment reference/narration
6. Webhook automatically processes their contribution

## Frontend Display Example:

```
┌─────────────────────────────────────────┐
│  Baby's Education Fund                  │
│  Saving for my baby's future education  │
├─────────────────────────────────────────┤
│  Progress: 25% (₦25,000 / ₦100,000)    │
│  [████████░░░░░░░░░░░░] 5 contributors │
├─────────────────────────────────────────┤
│  How to Contribute:                     │
│  1. Transfer to:                        │
│     Bank: Wema Bank                     │
│     Account: 1234567890                 │
│     Name: John Doe                      │
│                                         │
│  2. IMPORTANT - Use this reference:     │
│  ┌───────────────────────────────────┐ │
│  │ PL-abc123xyz-1699999999           │ │
│  └───────────────────────────────────┘ │
│  [📋 Copy Reference]                   │
│                                         │
│  Your contribution will be automatically│
│  tracked when you use this reference!   │
├─────────────────────────────────────────┤
│  Recent Contributors:                   │
│  • Jane Smith - ₦10,000                │
│  • Mike Johnson - ₦5,000               │
└─────────────────────────────────────────┘
```

## Note on Payment Reference:

The `payment_reference` changes with each page load (includes timestamp). This ensures:
- Each visitor gets a unique reference
- Prevents duplicate tracking issues
- Helps identify when the contribution was initiated

The format `PL-{token}-{timestamp}` is critical for the webhook to:
1. Recognize it as a payment link contribution
2. Match it to the correct payment link
3. Credit the appropriate goal/wallet
4. Create contribution record
5. Send notifications
