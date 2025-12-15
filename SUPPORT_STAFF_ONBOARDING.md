# GidiNest Support Staff Onboarding Guide

**Welcome to the GidiNest Support Team!**

This guide will help you get started as a customer support representative for GidiNest, our financial savings and wallet management platform.

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Getting Started](#getting-started)
3. [Support Dashboard](#support-dashboard)
4. [Handling Support Tickets](#handling-support-tickets)
5. [Common Support Scenarios](#common-support-scenarios)
6. [Escalation Procedures](#escalation-procedures)
7. [Best Practices](#best-practices)
8. [Resources & Tools](#resources--tools)

---

## Platform Overview

### What is GidiNest?

GidiNest is a financial platform that helps users save money, manage their wallets, and achieve their financial goals through:

- **Wallet Management** - Users can deposit and withdraw funds
- **Savings Goals** - Create and track savings targets with optional lock periods
- **Community Features** - Group savings challenges and community engagement
- **Secure Transactions** - PIN-protected withdrawals and transfers
- **Real-time Notifications** - Keep users informed of account activity

### Key Platform Features

#### Wallet Operations
- Users can deposit money via bank transfer to their virtual account
- Withdrawals require a transaction PIN for security
- All transactions are tracked and visible to users
- Automatic crediting via payment provider webhooks

#### Savings Goals
- Users can create multiple savings goals with custom targets
- Goals can have lock periods (maturity dates) to prevent early withdrawal
- Early withdrawals may incur penalties
- Funds can be transferred between wallet and savings goals
- Daily interest calculations (where applicable)
- Goals automatically unlock at maturity

#### User Verification
- Users verify their identity using BVN (Bank Verification Number)
- Verified users have full access to platform features
- Unverified users may have limited functionality

---

## Getting Started

### Your Support Dashboard Access

**URL:** `/internal-admin/support-dashboard/`

**Login Requirements:**
- You must have a staff account with `is_staff = True` permission
- Contact your team lead or administrator if you don't have access
- Use the same login as the Django admin panel

### First Day Checklist

- [ ] Receive your staff account credentials
- [ ] Log in to the support dashboard successfully
- [ ] Familiarize yourself with the dashboard layout
- [ ] Review this onboarding guide completely
- [ ] Shadow a senior support staff member (recommended)
- [ ] Review recent support tickets to understand common issues
- [ ] Set up your communication tools (email, Slack, etc.)
- [ ] Bookmark important resources and documentation

---

## Support Dashboard

The support dashboard is your command center. It provides real-time insights into platform health and user activity.

### Dashboard Sections

#### 1. User Metrics
**What you'll see:**
- Total users on the platform
- Active vs inactive users
- Verified vs unverified users
- New user signups (24 hours and 7 days)
- Users with BVN waiting for verification

**Why it matters:**
- Track platform growth
- Identify verification backlogs
- Spot unusual signup patterns

#### 2. Wallet & Transactions
**What you'll see:**
- Total balance across all wallets
- Total number of wallets
- Transactions in the last 24 hours
- Pending withdrawal requests
- Failed withdrawals (24 hours)

**Why it matters:**
- Monitor financial activity
- Identify stuck transactions
- Track failed withdrawals that may need attention

#### 3. Savings Goals
**What you'll see:**
- Number of active savings goals
- Total amount saved across all goals

**Why it matters:**
- Understand user engagement with savings features
- Track overall savings platform health

#### 4. Support Tickets (Customer Notes)
**What you'll see:**
- Open customer notes
- In-progress notes
- Flagged notes needing attention
- Urgent priority notes
- Notes created in last 24 hours
- Notes resolved in last 24 hours
- Breakdown by category (top 5)

**Why it matters:**
- **This is your primary work queue**
- Prioritize urgent and flagged tickets
- Track your team's response time

#### 5. Security Metrics
**What you'll see:**
- Active user sessions
- New sessions in last 24 hours

**Why it matters:**
- Monitor unusual session activity
- Detect potential security issues

#### 6. System Health
**What you'll see:**
- Errors logged in last 24 hours
- Error breakdown by request path

**Why it matters:**
- Identify system-wide issues
- Proactively address technical problems
- Know when to escalate to engineering

### Smart Alerts

The dashboard automatically highlights issues needing immediate attention:

1. **Urgent Customer Notes** - Red alert when urgent tickets exist
2. **Flagged Notes** - Yellow alert for tickets flagged for review
3. **High Pending Withdrawals** - When > 10 withdrawals are pending
4. **Failed Withdrawals Spike** - When > 5 withdrawals failed in 24h
5. **System Errors** - When > 50 errors logged in 24h
6. **Verification Backlog** - When > 20 users with BVN awaiting verification

**Action Required:** When you see an alert, investigate and take action immediately.

---

## Handling Support Tickets

### Customer Notes System

All support requests are tracked as "Customer Notes" in the admin panel.

### Ticket Statuses

- **Open** - New ticket, not yet assigned
- **In Progress** - Someone is working on it
- **Resolved** - Issue fixed, waiting for user confirmation
- **Closed** - Ticket completed and closed

### Ticket Priorities

- **Urgent** - Requires immediate attention (respond within 1 hour)
- **High** - Important issues (respond within 4 hours)
- **Normal** - Standard requests (respond within 24 hours)
- **Low** - General inquiries (respond within 48 hours)

### Ticket Categories

Common categories you'll encounter:

1. **Account Issues** - Login problems, password resets, verification
2. **Wallet Issues** - Deposit not credited, withdrawal failures, balance discrepancies
3. **Savings Issues** - Goal creation problems, transfer issues, unlock requests
4. **Transaction Issues** - Missing transactions, incorrect amounts, failed transfers
5. **Technical Issues** - App crashes, bugs, feature not working
6. **General Inquiry** - Questions about features, how-to guides
7. **Security Concerns** - Unauthorized access, suspicious activity
8. **Verification Issues** - BVN problems, document uploads, identity verification

### Your Workflow

#### Step 1: Review the Ticket
- Read the user's description carefully
- Check the ticket priority and category
- Review the user's account details in the admin panel

#### Step 2: Investigate
- Look up the user's account: `/admin/account/usermodel/`
- Check their wallet: `/admin/wallet/wallet/`
- Review recent transactions: `/admin/wallet/wallettransaction/`
- Check savings goals if applicable: `/admin/savings/savingsgoalmodel/`
- Review system logs if it's a technical issue

#### Step 3: Take Action
- Update ticket status to "In Progress"
- Add internal notes documenting your investigation
- Take necessary action (see Common Support Scenarios below)
- Communicate with the user clearly and professionally

#### Step 4: Resolve & Document
- Update the ticket status to "Resolved" or "Closed"
- Document the resolution in the ticket notes
- Follow up with the user if needed
- Flag the ticket if it requires escalation

---

## Common Support Scenarios

### 1. Deposit Not Credited

**User Complaint:** "I transferred money but it's not in my wallet"

**Steps to Resolve:**
1. Get transfer details from user (amount, date, time, account transferred from)
2. Check user's wallet transaction history
3. Check system logs for webhook failures
4. Verify with payment provider if needed
5. Manually credit if confirmed (requires manager approval)

**Response Time:** High priority - respond within 4 hours

**Escalate If:** Transaction confirmed but not in system after 24 hours

---

### 2. Withdrawal Failed

**User Complaint:** "My withdrawal failed but money was deducted"

**Steps to Resolve:**
1. Locate the withdrawal request in admin panel
2. Check withdrawal status and failure reason
3. Verify if funds were deducted from wallet
4. Refund to wallet if funds were deducted but withdrawal failed
5. Explain the issue and refund to the user

**Response Time:** Urgent - respond within 1 hour

**Escalate If:** System shows inconsistent state (deducted but no withdrawal record)

---

### 3. Forgot Transaction PIN

**User Complaint:** "I forgot my transaction PIN and can't withdraw"

**Steps to Resolve:**
1. Verify user identity (ask security questions, check verified status)
2. Use admin panel to reset transaction PIN
3. Generate temporary PIN or allow user to set new PIN
4. Confirm user received the PIN reset
5. Advise user to change PIN after first use

**Response Time:** High priority - respond within 4 hours

**Security Note:** Always verify identity before resetting PINs

---

### 4. Cannot Withdraw from Locked Goal

**User Complaint:** "I need money from my savings goal but it won't let me withdraw"

**Steps to Resolve:**
1. Check the savings goal details in admin panel
2. Verify if goal has a maturity date (lock period)
3. Check current date vs maturity date
4. Explain lock period policy to user
5. If emergency, escalate for early unlock approval (penalty may apply)

**Response Time:** Normal - respond within 24 hours

**Escalate If:** User has genuine emergency and needs early unlock

---

### 5. Account Verification Issues

**User Complaint:** "I submitted my BVN but I'm still not verified"

**Steps to Resolve:**
1. Check user's BVN status in admin panel
2. Verify BVN submission timestamp
3. Check for verification errors in logs
4. Manually verify if BVN is valid but system didn't auto-verify
5. Explain any issues with submitted information

**Response Time:** High priority - respond within 4 hours

**Escalate If:** BVN valid but system won't verify after 48 hours

---

### 6. Login Issues

**User Complaint:** "I can't log in to my account"

**Steps to Resolve:**
1. Verify user's email/phone number
2. Check if account is active (`is_active` field)
3. Check for recent failed login attempts
4. Send password reset link if needed
5. Check if account is locked for security reasons

**Response Time:** Urgent - respond within 1 hour

**Escalate If:** Account appears compromised or shows suspicious activity

---

### 7. Missing Transaction

**User Complaint:** "I don't see a transaction I made"

**Steps to Resolve:**
1. Get transaction details (amount, date, type, recipient)
2. Search wallet transactions for the user
3. Check if transaction was between wallet and savings goal
4. Verify transaction completed successfully
5. Explain where to find the transaction in the app

**Response Time:** High priority - respond within 4 hours

**Escalate If:** Transaction should exist but is completely missing from database

---

### 8. Duplicate Charge

**User Complaint:** "I was charged twice for the same thing"

**Steps to Resolve:**
1. Review user's transaction history
2. Identify the duplicate transactions
3. Verify if both transactions were processed
4. Refund one transaction if confirmed duplicate
5. Document the incident for engineering review

**Response Time:** Urgent - respond within 1 hour

**Escalate If:** Duplicate charges are system-wide or affecting multiple users

---

## Escalation Procedures

### When to Escalate

Escalate tickets to your team lead or engineering when:

1. **Technical Issues Beyond Your Scope**
   - Database errors or inconsistencies
   - System-wide bugs affecting multiple users
   - API integration failures

2. **Financial Discrepancies**
   - Large amounts missing or incorrectly credited
   - Potential fraud or suspicious activity
   - Withdrawal/deposit failures requiring manual intervention

3. **Security Concerns**
   - Suspected account compromise
   - Unauthorized transactions
   - Data breach reports

4. **Policy Exceptions**
   - Early withdrawal from locked goals
   - Refunds requiring manager approval
   - Account reinstatement after suspension

5. **User Threats or Legal Issues**
   - Legal threats or demands
   - Harassment or abusive behavior
   - Regulatory compliance questions

### How to Escalate

1. **Flag the Ticket** - Mark as "Flagged" in admin panel
2. **Update Priority** - Set to "Urgent" if needed
3. **Add Detailed Notes** - Document everything you've tried
4. **Notify Team Lead** - Via Slack/email with ticket link
5. **Set Expectations** - Tell user issue is escalated and when to expect response

### Escalation Response Times

- **Technical Issues:** 24 hours
- **Financial Issues:** 4 hours
- **Security Issues:** 1 hour
- **Legal Issues:** Immediate

---

## Best Practices

### Communication Guidelines

1. **Be Professional and Empathetic**
   - Use friendly, respectful language
   - Acknowledge user frustration
   - Avoid technical jargon unless necessary

2. **Be Clear and Concise**
   - Explain solutions step-by-step
   - Use bullet points for multiple steps
   - Include screenshots when helpful

3. **Set Realistic Expectations**
   - Give accurate timeframes
   - Under-promise and over-deliver
   - Follow up when promised

4. **Maintain User Privacy**
   - Never share user data with unauthorized parties
   - Use secure channels for sensitive information
   - Follow data protection regulations

### Response Templates

#### Acknowledging a Ticket
```
Hi [User Name],

Thank you for contacting GidiNest support. I've received your request regarding [issue description] and I'm looking into this for you right now.

I'll get back to you shortly with an update.

Best regards,
[Your Name]
GidiNest Support Team
```

#### Resolving a Ticket
```
Hi [User Name],

Good news! I've resolved the issue with [problem description].

[Explanation of what was done]

You should now be able to [expected outcome]. Please let me know if you have any other questions or if the issue persists.

Best regards,
[Your Name]
GidiNest Support Team
```

#### Escalating a Ticket
```
Hi [User Name],

Thank you for your patience. I've reviewed your case and I'm escalating this to our technical team for further investigation.

You can expect a response within [timeframe]. We'll keep you updated on the progress.

Best regards,
[Your Name]
GidiNest Support Team
```

### Daily Routine

**Start of Shift:**
1. Check support dashboard for alerts
2. Review urgent and flagged tickets
3. Check your assigned tickets
4. Attend team standup (if applicable)

**During Shift:**
5. Respond to tickets by priority (Urgent → High → Normal → Low)
6. Update ticket statuses regularly
7. Document all actions in ticket notes
8. Escalate when necessary

**End of Shift:**
9. Update all in-progress tickets with current status
10. Hand off urgent items to next shift
11. Review dashboard metrics
12. Report any trends or issues to team lead

### Performance Metrics

You'll be evaluated on:

- **Response Time** - How quickly you respond to tickets
- **Resolution Time** - How quickly you resolve issues
- **Customer Satisfaction** - User feedback and ratings
- **Ticket Volume** - Number of tickets handled
- **Escalation Rate** - How often you escalate (lower is better if resolved correctly)
- **Accuracy** - Correctness of resolutions

---

## Resources & Tools

### Admin Panel Sections

- **Users:** `/admin/account/usermodel/`
- **Wallets:** `/admin/wallet/wallet/`
- **Transactions:** `/admin/wallet/wallettransaction/`
- **Withdrawals:** `/admin/wallet/withdrawalrequest/`
- **Savings Goals:** `/admin/savings/savingsgoalmodel/`
- **Customer Notes:** `/admin/account/customernote/`
- **Sessions:** `/admin/account/usersession/`
- **Server Logs:** `/admin/core/serverlog/`

### Documentation

- **API Documentation:** `/api/docs/` (Swagger UI)
- **V2 API Status:** See `V2_IMPLEMENTATION_COMPLETE.md`
- **Support Dashboard Guide:** See `SUPPORT_DASHBOARD_FIXED.md`

### Helpful Django Admin Filters

When viewing lists in admin panel, use filters to narrow results:

- Filter by date ranges
- Filter by status (active, pending, resolved, etc.)
- Search by user email or phone number
- Sort by creation date or amount

### Common Admin Actions

- **Reset Password** - User changeform → "Force password reset" button
- **Verify User** - Set `is_verified = True`
- **Activate/Deactivate Account** - Toggle `is_active`
- **Reset Transaction PIN** - Wallet model → Update PIN field
- **Credit Wallet Manually** - Requires proper transaction record
- **Unlock Savings Goal** - Update maturity date or status

---

## Support Team Contacts

**Team Lead:** [Contact Information]
**Engineering Escalation:** [Contact Information]
**Finance/Payments Team:** [Contact Information]
**Security Team:** [Contact Information]

**Emergency Contact:** [24/7 On-call Number]

---

## FAQs for Support Staff

### Q: Can I manually credit a user's wallet?
**A:** Only with manager approval and proper documentation. Always verify the deposit was actually made before crediting.

### Q: How do I handle an angry or abusive user?
**A:** Remain professional, acknowledge their frustration, and focus on solving the problem. If abuse continues, escalate to team lead.

### Q: What if I accidentally gave wrong information?
**A:** Immediately correct the information in a new message, apologize for the confusion, and update the ticket notes. Inform your team lead if it's a significant error.

### Q: Can I unlock a savings goal for a user?
**A:** Not without escalation. Locked goals are a core platform feature. Escalate for manager approval with valid justification.

### Q: What if the issue is urgent but I don't know how to fix it?
**A:** Acknowledge the ticket immediately, escalate to team lead, and keep the user informed. Never leave urgent tickets unacknowledged.

### Q: How do I handle requests for refunds?
**A:** Document the request, verify the reason, and escalate to team lead for approval. Do not promise refunds without authorization.

---

## Getting Help

**Stuck on a ticket?**
- Check this guide first
- Search past tickets for similar issues
- Ask in team Slack channel
- Escalate to team lead if needed

**Found a bug?**
- Document it clearly with steps to reproduce
- Create a bug report ticket
- Tag it appropriately for engineering
- Inform team lead

**Need training?**
- Request shadowing with senior staff
- Ask for specific training on challenging areas
- Review past resolved tickets for learning
- Attend team knowledge-sharing sessions

---

## Welcome to the Team!

You're now part of the GidiNest support family. Your role is crucial in helping users achieve their financial goals. Remember:

- **Users trust us with their money** - Take every issue seriously
- **Communication is key** - Keep users informed
- **Ask for help** - No question is too small
- **Document everything** - It helps the whole team
- **Stay positive** - Your attitude affects user experience

**Thank you for joining GidiNest Support!**

---

**Document Version:** 1.0
**Last Updated:** December 10, 2025
**Questions?** Contact your team lead or [support-team@gidinest.com]
