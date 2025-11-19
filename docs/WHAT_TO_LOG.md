# What to Log - Comprehensive Guide

## Overview

The GidiNest server logs capture events across **ALL applications**, not just savings. This guide shows you what types of events you should log in each app.

## Currently Enabled Apps

All logs from these apps are automatically saved to the database:

✅ **account** - User accounts, authentication, profiles
✅ **wallet** - Wallets, transactions, deposits, withdrawals
✅ **savings** - Savings goals, contributions, withdrawals
✅ **onboarding** - Registration, email verification
✅ **community** - Posts, comments, community interactions
✅ **providers** - External APIs (Embedly, Paystack, Cuoral)
✅ **dashboard** - Dashboard analytics and metrics
✅ **transactions** - Transaction history and processing
✅ **notification** - Push notifications, emails, SMS
✅ **core** - Core utilities and helpers
✅ **celery** - Background tasks and scheduled jobs
✅ **django.request** - All HTTP 4xx and 5xx errors
✅ **django.db.backends** - Slow database queries

## What to Log in Each App

### 1. Account App (Authentication & Users)

#### Login/Logout
```python
import logging
logger = logging.getLogger(__name__)

# Successful login
logger.info(f"User logged in: {user.email}")

# Failed login
logger.warning(f"Failed login attempt for email: {email}")

# Multiple failed attempts
logger.warning(f"Multiple failed login attempts for {email} from IP {ip}")

# Account lockout
logger.error(f"Account locked due to too many failed attempts: {email}")

# Logout
logger.info(f"User logged out: {user.email}")
```

#### Registration
```python
# Successful registration
logger.info(f"New user registered: {user.email}")

# Registration failed
logger.error(f"Registration failed for {email}: {error}")

# Email verification sent
logger.info(f"Verification email sent to: {email}")

# Email verified
logger.info(f"Email verified for: {user.email}")
```

#### Profile Updates
```python
# Profile updated
logger.info(f"Profile updated by {user.email}")

# Password changed
logger.info(f"Password changed for {user.email}")

# Password reset requested
logger.warning(f"Password reset requested for {email}")

# Password reset completed
logger.info(f"Password reset completed for {user.email}")
```

#### KYC/Verification
```python
# BVN verification started
logger.info(f"BVN verification initiated for {user.email}")

# BVN verified
logger.info(f"BVN verified successfully for {user.email}: {bvn_number}")

# BVN verification failed
logger.error(f"BVN verification failed for {user.email}: {error}")

# NIN verification
logger.info(f"NIN verification completed for {user.email}")

# Document upload
logger.info(f"Document uploaded by {user.email}: {document_type}")
```

#### Account Tier Changes
```python
# Tier upgraded
logger.info(f"Account tier upgraded for {user.email}: {old_tier} -> {new_tier}")

# Tier upgrade failed
logger.warning(f"Tier upgrade failed for {user.email}: {reason}")
```

### 2. Wallet App

#### Account Creation
```python
# Virtual account created
logger.info(f"Virtual account created for {user.email}: {account_number} ({bank})")

# Account creation failed
logger.error(f"Virtual account creation failed for {user.email}: {error}")
```

#### Deposits
```python
# Deposit received
logger.info(f"Deposit: ₦{amount} to {wallet.account_number} by {user.email}")

# Webhook received
logger.info(f"Paystack webhook received: {event_type}, reference: {reference}")

# Webhook processing failed
logger.error(f"Webhook processing failed for {reference}: {error}")

# Duplicate deposit attempt
logger.warning(f"Duplicate deposit detected: {reference}")
```

#### Withdrawals
```python
# Withdrawal requested
logger.info(f"Withdrawal requested: ₦{amount} from {user.email} to {account_number}")

# Insufficient balance
logger.warning(f"Withdrawal failed - insufficient balance for {user.email}")

# Withdrawal successful
logger.info(f"Withdrawal completed: ₦{amount} for {user.email}, ref: {reference}")

# Withdrawal failed
logger.error(f"Withdrawal failed for {user.email}: {error}")
```

#### Transfers
```python
# Internal transfer
logger.info(f"Transfer: ₦{amount} from {sender.email} to {recipient.email}")

# External transfer initiated
logger.info(f"External transfer initiated: ₦{amount} by {user.email} to {bank}/{account}")
```

### 3. Savings App

#### Goal Management
```python
# Goal created
logger.info(f"Savings goal created by {user.email}: '{goal.name}', target: ₦{goal.target_amount}")

# Goal updated
logger.info(f"Savings goal '{goal.name}' updated by {user.email}")

# Goal deleted
logger.info(f"Savings goal '{goal.name}' deleted by {user.email}")

# Goal completed
logger.info(f"Savings goal '{goal.name}' reached target by {user.email}")
```

#### Contributions
```python
# Contribution made
logger.info(f"Contribution: ₦{amount} to '{goal.name}' by {user.email}")

# Large contribution
logger.info(f"Large contribution: ₦{amount} to '{goal.name}' by {user.email}")

# Contribution exceeds target
logger.warning(f"Contribution exceeds target for '{goal.name}' by {user.email}")

# Contribution failed
logger.error(f"Contribution failed for '{goal.name}' by {user.email}: {error}")
```

#### Withdrawals
```python
# Withdrawal from goal
logger.info(f"Withdrawal: ₦{amount} from '{goal.name}' by {user.email}")

# Insufficient funds in goal
logger.warning(f"Withdrawal failed - insufficient funds in '{goal.name}' for {user.email}")

# Premature withdrawal
logger.warning(f"Early withdrawal from '{goal.name}' by {user.email}")
```

#### Interest
```python
# Interest accrued
logger.info(f"Interest accrued: ₦{interest} on '{goal.name}' for {user.email}")

# Interest calculation error
logger.error(f"Interest calculation failed for goal {goal.id}: {error}")
```

### 4. Transactions App

```python
# Transaction created
logger.info(f"Transaction created: {tx_id}, type: {tx_type}, amount: ₦{amount}")

# Transaction processing
logger.info(f"Processing transaction {tx_id}")

# Transaction completed
logger.info(f"Transaction {tx_id} completed successfully")

# Transaction failed
logger.error(f"Transaction {tx_id} failed at step '{step}': {error}")

# Transaction reversed
logger.warning(f"Transaction {tx_id} reversed for {user.email}")
```

### 5. Community App

```python
# Post created
logger.info(f"Community post created by {user.email}: '{post.title}'")

# Post updated
logger.info(f"Post updated by {user.email}: {post.id}")

# Post deleted
logger.info(f"Post deleted by {user.email}: {post.id}")

# Comment added
logger.info(f"Comment added by {user.email} on post {post.id}")

# Post flagged
logger.warning(f"Post {post.id} flagged by {user.email} for: {reason}")

# User blocked
logger.warning(f"User {blocked_user.email} blocked by {user.email}")
```

### 6. Notification App

```python
# Push notification sent
logger.info(f"Push notification sent to {user.email}: '{title}'")

# Push notification failed
logger.error(f"Push notification failed for {user.email}: {error}")

# Email notification sent
logger.info(f"Email sent to {user.email}: {subject}")

# Email failed
logger.error(f"Email failed for {user.email}: {error}")

# SMS sent
logger.info(f"SMS sent to {phone}: {message}")

# FCM token registered
logger.info(f"FCM token registered for {user.email}: {device_id}")
```

### 7. Providers App (External APIs)

#### Embedly/Banking
```python
# API call started
logger.info(f"Embedly API call: {endpoint}")

# API call successful
logger.info(f"Embedly: Virtual account created - {account_number}")

# API call failed
logger.error(f"Embedly API error: {error_message}", exc_info=True)

# Rate limit hit
logger.warning(f"Embedly rate limit exceeded")
```

#### Paystack
```python
# Payment initialized
logger.info(f"Paystack payment initialized: {reference}, amount: ₦{amount}")

# Payment verified
logger.info(f"Paystack payment verified: {reference}")

# Payment failed
logger.error(f"Paystack payment failed: {reference}, reason: {message}")
```

#### Cuoral (NIN Verification)
```python
# NIN verification started
logger.info(f"NIN verification started for {user.email}")

# NIN verified
logger.info(f"NIN verified for {user.email}: {nin}")

# NIN verification failed
logger.warning(f"NIN verification failed for {user.email}: {error}")
```

### 8. Dashboard App

```python
# Analytics generated
logger.info(f"Dashboard analytics generated for {user.email}")

# Report generated
logger.info(f"Financial report generated for {user.email}")

# Export created
logger.info(f"Transaction export created for {user.email}: {format}")
```

### 9. Celery Tasks (Background Jobs)

```python
# Task started
logger.info(f"Celery task started: {task_name}")

# Task completed
logger.info(f"Celery task completed: {task_name}, duration: {duration}s")

# Task failed
logger.error(f"Celery task failed: {task_name}, error: {error}", exc_info=True)

# Scheduled task
logger.info(f"Daily interest calculation started for {count} users")

# Cron job
logger.info(f"Scheduled report generation completed")
```

## Security Events to Log

### Suspicious Activity
```python
# Brute force attempts
logger.critical(f"Potential brute force attack from IP {ip}: {attempt_count} attempts")

# Unusual login location
logger.warning(f"Login from unusual location for {user.email}: {country}, IP: {ip}")

# Account takeover attempt
logger.critical(f"Suspicious activity detected for {user.email}: {reason}")

# Rate limit exceeded
logger.warning(f"Rate limit exceeded for {user.email} on {endpoint}")
```

### Permission Violations
```python
# Unauthorized access
logger.warning(f"Unauthorized access attempt by {user.email} to {resource}")

# Admin action
logger.info(f"Admin {admin.email} performed: {action} on user {user.email}")

# Data export
logger.warning(f"User data exported by {admin.email} for {user.email}")
```

## Best Practices

### 1. Use Appropriate Log Levels

- **DEBUG** - Detailed diagnostic info (not saved to database)
- **INFO** - Successful operations, normal events
- **WARNING** - Potential issues, unusual behavior
- **ERROR** - Errors that need attention
- **CRITICAL** - Severe errors, security incidents

### 2. Include Context

Always include:
- User email/ID
- Amount (for financial operations)
- Reference IDs
- Error messages
- IP addresses (for security events)

### 3. Don't Log Sensitive Data

❌ **DON'T LOG:**
- Passwords
- Full card numbers
- PIN codes
- API keys/secrets
- Session tokens

✅ **DO LOG:**
- User emails
- Account numbers (last 4 digits)
- Transaction references
- BVN (last 4 digits)
- Error messages

### 4. Use exc_info for Exceptions

```python
try:
    # Some code
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)  # Captures full traceback
```

## Viewing Logs

All these logs are viewable in the admin panel at:
`https://app.gidinest.com/internal-admin/core/serverlog/`

You can:
- Filter by app (account, wallet, savings, etc.)
- Filter by level (INFO, WARNING, ERROR, CRITICAL)
- Search by user email, message, IP, etc.
- View full exception tracebacks
- See statistics and trends

## Performance Tips

1. **Avoid logging in loops** - Batch operations instead
2. **Use INFO level** - Not DEBUG (DEBUG not saved to DB anyway)
3. **Be concise** - Keep messages short and meaningful
4. **Clean old logs** - Run `python manage.py cleanup_logs` regularly

## Examples in Views

```python
import logging
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)  # Uses app name automatically

class MyAPIView(APIView):
    def post(self, request):
        user = request.user

        try:
            # Log the start
            logger.info(f"User {user.email} initiated {action}")

            # Your business logic
            result = do_something()

            # Log success
            logger.info(f"Action completed successfully for {user.email}")

            return Response({"success": True})

        except ValueError as e:
            # Log business logic errors
            logger.warning(f"Invalid input from {user.email}: {str(e)}")
            return Response({"error": str(e)}, status=400)

        except Exception as e:
            # Log unexpected errors with full traceback
            logger.error(f"Unexpected error for {user.email}: {str(e)}", exc_info=True)
            return Response({"error": "Internal error"}, status=500)
```

## Summary

The server logs system captures events from **all apps** in your system:

- ✅ All HTTP errors (4xx, 5xx)
- ✅ User authentication and actions
- ✅ Financial transactions
- ✅ External API calls
- ✅ Security events
- ✅ Background tasks
- ✅ Errors and exceptions

Start adding logging to your views and you'll be able to monitor everything that happens in your application!
