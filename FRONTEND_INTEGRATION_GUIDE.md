# Frontend Integration Guide - V2 KYC + 9PSB Wallet

**Last Updated:** 2025-12-15
**Target:** Mobile App / Web Frontend

---

## 🎯 Overview

This guide shows how to integrate the new V2 KYC flow (Prembly) and 9PSB wallet creation into your frontend application.

**Complete User Journey:**
```
Register → Login → Verify BVN → Confirm BVN → Get Wallet → Receive Deposits
```

---

## 📱 Complete Frontend Flow

### Step 1: User Registration (Existing)

**Endpoint:** `POST /api/v2/auth/register`

```javascript
const register = async (userData) => {
  const response = await fetch('http://localhost:8000/api/v2/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: userData.email,
      password: userData.password,
      first_name: userData.firstName,
      last_name: userData.lastName,
      phone: userData.phone
    })
  });

  const data = await response.json();

  if (data.success) {
    // Save tokens
    localStorage.setItem('access_token', data.data.access);
    localStorage.setItem('refresh_token', data.data.refresh);
    return data.data;
  }

  throw new Error(data.error?.message || 'Registration failed');
};
```

### Step 2: BVN Verification (NEW - V2)

**Endpoint:** `POST /api/v2/kyc/bvn/verify`

This is a **two-step process**:

#### 2.1 Verify BVN (Step 1)

```javascript
const verifyBVN = async (bvn) => {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/v2/kyc/bvn/verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ bvn })
  });

  const data = await response.json();

  if (data.success) {
    // BVN verified! Show details to user for confirmation
    return data.data.details;
    /*
    {
      first_name: "John",
      last_name: "Doe",
      middle_name: "William",
      date_of_birth: "15-Jan-1990",
      phone_number: "08012345678",
      email: "john.doe@example.com",
      gender: "Male",
      state_of_residence: "Lagos",
      enrollment_bank: "Access Bank",
      watch_listed: "false"
    }
    */
  }

  throw new Error(data.error?.message || 'BVN verification failed');
};
```

**Frontend UI:**
```jsx
// Show BVN details in a confirmation screen
<div className="bvn-confirmation">
  <h2>Confirm Your BVN Details</h2>
  <p>Name: {details.first_name} {details.middle_name} {details.last_name}</p>
  <p>Date of Birth: {details.date_of_birth}</p>
  <p>Phone: {details.phone_number}</p>
  <p>State: {details.state_of_residence}</p>

  <button onClick={handleConfirm}>Confirm & Continue</button>
  <button onClick={handleCancel}>Cancel</button>
</div>
```

#### 2.2 Confirm BVN (Step 2) - Creates Wallet! ✨

```javascript
const confirmBVN = async (bvn, confirmed = true) => {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/v2/kyc/bvn/confirm', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ bvn, confirmed })
  });

  const data = await response.json();

  if (data.success) {
    // BVN confirmed! User is now Tier 1
    // Wallet may be created automatically
    return data.data;
    /*
    {
      is_verified: true,
      verification_method: "bvn",
      verification_status: "verified",
      account_tier: "Tier 1",
      message: "BVN verified successfully! You now have Tier 1 access",
      limits: {
        daily_limit: 50000000,
        per_transaction_limit: 20000000,
        monthly_limit: 500000000
      },
      wallet: {  // ✨ NEW! Wallet created automatically
        created: true,
        account_number: "0123456789",
        bank: "9PSB",
        message: "Virtual wallet created successfully! You can now receive deposits."
      }
    }
    */
  }

  throw new Error(data.error?.message || 'BVN confirmation failed');
};
```

**Frontend Success Screen:**
```jsx
// Show success message with wallet details
<div className="success-screen">
  <h2>✅ Verification Complete!</h2>
  <p>{data.message}</p>

  <div className="account-tier">
    <h3>Account Tier: {data.account_tier}</h3>
    <p>Daily Limit: ₦{formatMoney(data.limits.daily_limit)}</p>
    <p>Per Transaction: ₦{formatMoney(data.limits.per_transaction_limit)}</p>
  </div>

  {data.wallet && data.wallet.created && (
    <div className="wallet-created">
      <h3>🎉 Wallet Created!</h3>
      <p className="account-number">{data.wallet.account_number}</p>
      <p className="bank-name">{data.wallet.bank}</p>
      <button onClick={() => navigate('/wallet')}>View Wallet</button>
    </div>
  )}

  <button onClick={() => navigate('/dashboard')}>Go to Dashboard</button>
</div>
```

### Step 3: View Wallet Details

**Endpoint:** `GET /api/v2/wallet/`

```javascript
const getWalletDetails = async () => {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/v2/wallet/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json();

  if (data.success) {
    return data.data;
    /*
    {
      wallet: {
        balance: "0.00",
        account_number: "0123456789",
        bank: "9PSB",
        bank_code: "120001",
        account_name: "John Doe",
        currency: "NGN",
        created_at: "2025-12-15T10:00:00Z"
      },
      savings_goals: [],
      transaction_pin_set: false
    }
    */
  }

  throw new Error(data.error?.message || 'Failed to fetch wallet');
};
```

**Frontend Wallet Screen:**
```jsx
function WalletScreen() {
  const [wallet, setWallet] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getWalletDetails()
      .then(data => {
        setWallet(data.wallet);
        setLoading(false);
      })
      .catch(error => {
        console.error(error);
        setLoading(false);
      });
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="wallet-screen">
      <h1>My Wallet</h1>

      <div className="balance-card">
        <p className="label">Available Balance</p>
        <h2 className="balance">₦{formatMoney(wallet.balance)}</h2>
      </div>

      <div className="account-details">
        <h3>Account Details</h3>
        <div className="detail-row">
          <span>Account Number:</span>
          <span className="account-number">
            {wallet.account_number}
            <button onClick={() => copyToClipboard(wallet.account_number)}>
              Copy
            </button>
          </span>
        </div>
        <div className="detail-row">
          <span>Account Name:</span>
          <span>{wallet.account_name}</span>
        </div>
        <div className="detail-row">
          <span>Bank:</span>
          <span>{wallet.bank}</span>
        </div>
      </div>

      <div className="actions">
        <button onClick={() => navigate('/wallet/deposit')}>
          Add Money
        </button>
        <button onClick={() => navigate('/wallet/withdraw')}>
          Withdraw
        </button>
      </div>
    </div>
  );
}
```

### Step 4: Deposit Instructions

**Endpoint:** `POST /api/v2/wallet/deposit`

```javascript
const getDepositInstructions = async (amount) => {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/v2/wallet/deposit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ amount })
  });

  const data = await response.json();

  if (data.success) {
    return data.data;
    /*
    {
      account_number: "0123456789",
      account_name: "John Doe",
      bank_name: "9PSB",
      bank_code: "120001",
      amount: "10000.00",
      currency: "NGN",
      instructions: [
        "Transfer the amount to the account above",
        "Your wallet will be credited automatically",
        "Credit typically happens within 1-5 minutes",
        "Use any banking app or USSD to make the transfer"
      ]
    }
    */
  }

  throw new Error(data.error?.message || 'Failed to get deposit instructions');
};
```

**Frontend Deposit Screen:**
```jsx
function DepositScreen() {
  const [amount, setAmount] = useState('');
  const [instructions, setInstructions] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleDeposit = async () => {
    if (!amount || amount <= 0) {
      alert('Please enter a valid amount');
      return;
    }

    setLoading(true);
    try {
      const data = await getDepositInstructions(amount);
      setInstructions(data);
    } catch (error) {
      alert(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (instructions) {
    return (
      <div className="deposit-instructions">
        <h2>Transfer ₦{formatMoney(instructions.amount)}</h2>

        <div className="account-details-card">
          <div className="detail">
            <label>Account Number</label>
            <div className="value">
              <span className="account-number">{instructions.account_number}</span>
              <button onClick={() => copyToClipboard(instructions.account_number)}>
                Copy
              </button>
            </div>
          </div>

          <div className="detail">
            <label>Account Name</label>
            <span>{instructions.account_name}</span>
          </div>

          <div className="detail">
            <label>Bank</label>
            <span>{instructions.bank_name}</span>
          </div>
        </div>

        <div className="instructions">
          <h3>Instructions:</h3>
          <ol>
            {instructions.instructions.map((instruction, index) => (
              <li key={index}>{instruction}</li>
            ))}
          </ol>
        </div>

        <button onClick={() => navigate('/wallet')}>
          Done - Go Back to Wallet
        </button>
      </div>
    );
  }

  return (
    <div className="deposit-screen">
      <h2>Add Money to Wallet</h2>

      <div className="amount-input">
        <label>Enter Amount</label>
        <input
          type="number"
          placeholder="0.00"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </div>

      <button onClick={handleDeposit} disabled={loading}>
        {loading ? 'Loading...' : 'Continue'}
      </button>
    </div>
  );
}
```

---

## 🔄 Real-Time Balance Updates

### Option 1: Polling (Simple)

```javascript
// Poll wallet balance every 10 seconds
useEffect(() => {
  const interval = setInterval(() => {
    getWalletDetails().then(data => {
      setWallet(data.wallet);
    });
  }, 10000); // 10 seconds

  return () => clearInterval(interval);
}, []);
```

### Option 2: WebSocket (Advanced)

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/wallet/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'wallet_credit') {
    // Update balance immediately
    setWallet(prev => ({
      ...prev,
      balance: data.new_balance
    }));

    // Show notification
    showNotification(`Wallet credited: ₦${data.amount}`);
  }
};
```

---

## 🧪 Testing the Complete Flow

### Test Script (JavaScript)

```javascript
// test-v2-flow.js
const BASE_URL = 'http://localhost:8000';
let accessToken = null;

async function testCompleteFlow() {
  console.log('🧪 Starting V2 Flow Test...\n');

  // 1. Register
  console.log('1️⃣ Registering user...');
  const registerRes = await fetch(`${BASE_URL}/api/v2/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: `test${Date.now()}@example.com`,
      password: 'SecurePass123!',
      first_name: 'Test',
      last_name: 'User',
      phone: '08012345678'
    })
  });
  const registerData = await registerRes.json();
  console.log('✅ Registered:', registerData.data.user.email);
  accessToken = registerData.data.access;

  // 2. Verify BVN
  console.log('\n2️⃣ Verifying BVN...');
  const verifyRes = await fetch(`${BASE_URL}/api/v2/kyc/bvn/verify`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ bvn: '22222222222' })
  });
  const verifyData = await verifyRes.json();
  console.log('✅ BVN Verified:', verifyData.data.details.first_name, verifyData.data.details.last_name);

  // 3. Confirm BVN (Creates Wallet!)
  console.log('\n3️⃣ Confirming BVN...');
  const confirmRes = await fetch(`${BASE_URL}/api/v2/kyc/bvn/confirm`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ bvn: '22222222222', confirmed: true })
  });
  const confirmData = await confirmRes.json();
  console.log('✅ BVN Confirmed!');
  console.log('   Account Tier:', confirmData.data.account_tier);

  if (confirmData.data.wallet) {
    console.log('🎉 Wallet Created!');
    console.log('   Account Number:', confirmData.data.wallet.account_number);
    console.log('   Bank:', confirmData.data.wallet.bank);
  }

  // 4. Get Wallet Details
  console.log('\n4️⃣ Fetching wallet details...');
  const walletRes = await fetch(`${BASE_URL}/api/v2/wallet/`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  const walletData = await walletRes.json();
  console.log('✅ Wallet Details:');
  console.log('   Balance:', walletData.data.wallet.balance);
  console.log('   Account:', walletData.data.wallet.account_number);

  // 5. Get Deposit Instructions
  console.log('\n5️⃣ Getting deposit instructions...');
  const depositRes = await fetch(`${BASE_URL}/api/v2/wallet/deposit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ amount: 10000 })
  });
  const depositData = await depositRes.json();
  console.log('✅ Deposit Instructions:');
  console.log('   Transfer ₦10,000 to:', depositData.data.account_number);
  console.log('   Account Name:', depositData.data.account_name);

  console.log('\n🎉 Test Complete!\n');
}

testCompleteFlow().catch(console.error);
```

Run:
```bash
node test-v2-flow.js
```

---

## 📲 React Native Example

```jsx
import React, { useState } from 'react';
import { View, Text, TextInput, Button, Alert } from 'react-native';

function BVNVerificationScreen({ navigation }) {
  const [bvn, setBvn] = useState('');
  const [loading, setLoading] = useState(false);
  const [details, setDetails] = useState(null);

  const handleVerify = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v2/kyc/bvn/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ bvn })
      });

      const data = await response.json();

      if (data.success) {
        setDetails(data.data.details);
      } else {
        Alert.alert('Error', data.error?.message || 'Verification failed');
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v2/kyc/bvn/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ bvn, confirmed: true })
      });

      const data = await response.json();

      if (data.success) {
        Alert.alert(
          'Success!',
          data.data.message,
          [{ text: 'OK', onPress: () => navigation.navigate('Wallet') }]
        );
      } else {
        Alert.alert('Error', data.error?.message || 'Confirmation failed');
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  if (details) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Confirm Your Details</Text>
        <Text>Name: {details.first_name} {details.last_name}</Text>
        <Text>DOB: {details.date_of_birth}</Text>
        <Text>Phone: {details.phone_number}</Text>
        <Button title="Confirm" onPress={handleConfirm} disabled={loading} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Verify Your BVN</Text>
      <TextInput
        style={styles.input}
        placeholder="Enter BVN (11 digits)"
        value={bvn}
        onChangeText={setBvn}
        keyboardType="number-pad"
        maxLength={11}
      />
      <Button title="Verify" onPress={handleVerify} disabled={loading} />
    </View>
  );
}
```

---

## 🔔 Handling Notifications

When a deposit is received, the backend sends notifications. Handle them in your frontend:

```javascript
// Listen for push notifications
import PushNotification from 'react-native-push-notification';

PushNotification.configure({
  onNotification: function (notification) {
    if (notification.data?.type === 'wallet_credit') {
      // Refresh wallet balance
      getWalletDetails().then(data => {
        setWallet(data.wallet);
      });

      // Show toast
      showToast(`Wallet credited: ₦${notification.data.amount}`);
    }
  }
});
```

---

## ⚠️ Error Handling

```javascript
async function handleAPICall(apiFunction) {
  try {
    const result = await apiFunction();
    return { success: true, data: result };
  } catch (error) {
    // Handle different error codes
    if (error.message.includes('KYC_BVN_ALREADY_VERIFIED')) {
      return {
        success: false,
        error: 'BVN already verified',
        code: 'ALREADY_VERIFIED'
      };
    }

    if (error.message.includes('KYC_SESSION_EXPIRED')) {
      return {
        success: false,
        error: 'Session expired. Please verify again.',
        code: 'SESSION_EXPIRED'
      };
    }

    return {
      success: false,
      error: error.message,
      code: 'UNKNOWN_ERROR'
    };
  }
}
```

---

## ✅ Testing Checklist

- [ ] User can register
- [ ] User can verify BVN
- [ ] BVN details display correctly
- [ ] User can confirm BVN
- [ ] Success message shows account tier
- [ ] Wallet creation confirmed in response
- [ ] Wallet screen shows account number
- [ ] Account number is copyable
- [ ] Deposit instructions display
- [ ] Balance updates after deposit
- [ ] Notifications work

---

## 🚀 Ready to Deploy

Your frontend is now ready to integrate with the V2 KYC and 9PSB wallet system!

**Remember:**
- Replace `localhost:8000` with your actual API URL
- Handle token refresh for long sessions
- Test with real Prembly BVN in staging
- Test deposits with 9PSB test account

---

**Questions?** Check the API docs or test with the provided scripts!
