# GidiNest: Predictive Maternal Health Risk Platform

## Positioning Statement

> "A predictive maternal health risk platform that converts financial behaviour and saving patterns into early indicators of care disruption risk for mothers in underserved and climate-vulnerable environments."

---

## 1. The Core Insight

**Financial behavior is a proxy for healthcare access.**

When a mother in an underserved community:
- Stops saving → She may be experiencing financial stress
- Makes unexpected withdrawals → Emergency situation, may skip prenatal care
- Misses contribution patterns → Income disruption, healthcare becomes deprioritized
- Abandons savings goals → Life crisis, high risk of care dropout

**We don't need clinical data to predict care disruption. We can see it in the money.**

---

## 2. Why This Matters (MIT Solve Framing)

### The Problem
- 70% of maternal deaths occur in sub-Saharan Africa and South Asia
- Most deaths are preventable with consistent prenatal care
- Women don't stop going to clinics because they don't care — they stop because they can't afford to
- Climate events (floods, droughts) disproportionately affect maternal health access

### The Gap
- Health systems wait for women to miss appointments (reactive)
- No early warning when financial stress will cause care disruption
- Community health workers don't know who to prioritize

### GidiNest's Unique Position
- We see financial behavior BEFORE it affects healthcare
- We're already embedded in mothers' daily financial lives
- We can predict risk weeks before a missed clinic visit

---

## 3. Data We Already Capture

### A. Maternal Journey Data
| Field | What It Tells Us |
|-------|------------------|
| `journey_type` | Pregnant / Trying to Conceive / New Mom |
| `pregnancy_weeks` | Current gestational age (0-42 weeks) |
| `due_date` | Expected delivery date |
| `hospital_plan` | Basic (public) / Private / Premium — affordability indicator |
| `location` | Geographic access to healthcare |
| `baby_essentials_preference` | Socioeconomic indicator |

### B. Financial Behavior Data
| Field | What It Tells Us |
|-------|------------------|
| Savings goal progress | Preparedness for maternal expenses |
| Contribution frequency | Financial discipline & stability |
| Withdrawal patterns | Emergency indicators |
| Wallet balance over time | Financial buffer for healthcare |
| Transaction history | Income regularity |

### C. Engagement Data
| Field | What It Tells Us |
|-------|------------------|
| App login frequency | Engagement with maternal planning |
| Community group membership | Support network strength |
| Notification response | Responsiveness to health reminders |
| Goal completion rate | Follow-through behavior |

---

## 4. The Risk Scoring Model

### Risk Categories

```
OVERALL RISK SCORE = weighted average of:
├── Financial Stability Risk (40%)
├── Healthcare Access Risk (25%)
├── Engagement Risk (20%)
└── Timeline Risk (15%)
```

### 4.1 Financial Stability Risk (40% weight)

**Signals:**
- Savings rate decline >30% from baseline → HIGH RISK
- Wallet balance below 2-week healthcare cost → MEDIUM RISK
- Unexpected withdrawal >50% of savings → HIGH RISK
- Missed 2+ consecutive contributions → MEDIUM RISK
- Zero savings activity for 2+ weeks → HIGH RISK

**Scoring:**
```
0-20:  Low risk (stable finances)
21-50: Medium risk (monitor)
51-80: High risk (intervention needed)
81-100: Critical (immediate outreach)
```

### 4.2 Healthcare Access Risk (25% weight)

**Signals:**
- Hospital plan = "Basic/Public" + Low savings → HIGH RISK
- Location in underserved area → ELEVATED RISK
- No savings goal for healthcare → MEDIUM RISK
- Climate event in region (flood/drought) → ELEVATED RISK

### 4.3 Engagement Risk (20% weight)

**Signals:**
- No app login for 7+ days → MEDIUM RISK
- No community engagement → ELEVATED RISK
- Ignoring notifications → MEDIUM RISK
- Abandoned onboarding → HIGH RISK

### 4.4 Timeline Risk (15% weight)

**Signals:**
- Third trimester (28+ weeks) + any other risk → AMPLIFIED
- Within 4 weeks of due date + low savings → CRITICAL
- Overdue (past due date) + disengaged → CRITICAL

---

## 5. Early Warning Triggers

### Automatic Alerts

| Trigger | Risk Level | Action |
|---------|------------|--------|
| Savings stopped for 2 weeks | Medium | In-app nudge + SMS |
| Large unexpected withdrawal | High | Phone call from support |
| 3rd trimester + low balance | High | Connect to community health worker |
| No activity for 14 days | Critical | Home visit referral |
| Climate event in user's region | Elevated | Proactive check-in |

### Intervention Cascade

```
Level 1: Automated (App notification, SMS)
    ↓ No response in 48 hours
Level 2: Personal (Phone call from GidiNest team)
    ↓ No response in 72 hours
Level 3: Community (Alert community health worker)
    ↓ No response in 1 week
Level 4: Emergency (Home visit, connect to NGO partner)
```

---

## 6. Climate Vulnerability Layer

### How Climate Affects Maternal Health Access

1. **Floods** → Roads impassable → Can't reach clinic
2. **Drought** → Crop failure → No income → Can't afford care
3. **Heat waves** → Increased pregnancy complications
4. **Economic shocks** → Food prices rise → Healthcare deprioritized

### Integration Approach

- Partner with climate data providers (e.g., FEWS NET, ACLED)
- Map user locations to climate vulnerability indices
- Increase risk scores when climate events affect user's region
- Proactive outreach before/during climate events

---

## 7. What Needs To Be Built

### Phase 1: Risk Scoring Engine (MVP)
- [ ] Risk score calculation algorithm
- [ ] Database model to store risk scores and history
- [ ] Daily/weekly batch job to recalculate scores
- [ ] Admin dashboard to view at-risk mothers

### Phase 2: Alert System
- [ ] Automated trigger detection
- [ ] Alert routing to appropriate channel (SMS, call, CHW)
- [ ] Escalation workflow
- [ ] Response tracking

### Phase 3: Health Worker Integration
- [ ] Community Health Worker (CHW) portal
- [ ] Risk-prioritized patient list for CHWs
- [ ] Visit tracking and outcome recording
- [ ] Two-way communication with mothers

### Phase 4: Climate Integration
- [ ] Climate data API integration
- [ ] Geographic risk mapping
- [ ] Predictive alerts before climate events
- [ ] Emergency resource allocation

### Phase 5: Outcomes Tracking
- [ ] Health outcome data collection (optional self-report)
- [ ] Model validation and refinement
- [ ] Impact measurement for reporting

---

## 8. Technical Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                            │
├─────────────────────────────────────────────────────────────┤
│  GidiNest App    │  Climate APIs   │  Health Partner APIs   │
│  - Savings data  │  - Weather      │  - CHW assignments     │
│  - Transactions  │  - Disasters    │  - Clinic visits       │
│  - Engagement    │  - Food security│  - Outcomes            │
└────────┬─────────┴────────┬────────┴──────────┬─────────────┘
         │                  │                   │
         ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                 RISK SCORING ENGINE                         │
├─────────────────────────────────────────────────────────────┤
│  1. Data aggregation (daily/weekly)                         │
│  2. Feature extraction (savings patterns, engagement)       │
│  3. Risk score calculation (weighted algorithm)             │
│  4. Trend analysis (is risk increasing?)                    │
│  5. Trigger detection (threshold breaches)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 INTERVENTION SYSTEM                         │
├─────────────────────────────────────────────────────────────┤
│  Alert Queue → Notification Service → Escalation Engine     │
│       │              │                      │               │
│       ▼              ▼                      ▼               │
│   In-App         SMS/Email           CHW Assignment         │
│   Nudges         Alerts              & Home Visits          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 DASHBOARDS & REPORTING                      │
├─────────────────────────────────────────────────────────────┤
│  Admin Dashboard    │  CHW Mobile App   │  Impact Reports   │
│  - At-risk list     │  - Patient list   │  - Outcomes       │
│  - Trend graphs     │  - Visit logging  │  - Model accuracy │
│  - Interventions    │  - Communication  │  - Coverage       │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. How To Spin This for MIT Solve

### Key Messages

1. **We're not building new infrastructure** — we're leveraging existing financial behavior data that mothers already generate through our savings platform.

2. **Predictive, not reactive** — Health systems wait for missed appointments. We predict care disruption before it happens.

3. **Financially sustainable** — The platform is built on top of a revenue-generating fintech (GidiNest savings), not dependent on grants.

4. **Climate-aware** — We layer climate vulnerability data to identify mothers at highest risk during environmental shocks.

5. **Community-integrated** — We connect digital signals to human intervention through community health workers.

### Unique Value Proposition

> "GidiNest turns every savings transaction into a health signal. When a pregnant mother's financial behavior changes, we see it weeks before she misses a clinic visit — giving us time to intervene."

### Impact Metrics to Promise

- **Leading indicator:** Financial stress detected X days before care disruption
- **Coverage:** X pregnant women monitored through savings behavior
- **Intervention rate:** X% of at-risk mothers reached before missing care
- **Outcome improvement:** X% reduction in care dropout among flagged users

---

## 10. Partnerships Needed

| Partner Type | Purpose | Examples |
|--------------|---------|----------|
| Climate Data | Vulnerability mapping | FEWS NET, Climate Hazards Center |
| Health NGOs | CHW networks, last-mile delivery | Living Goods, BRAC, Last Mile Health |
| Government | Health system integration | State Primary Health Care Boards |
| Research | Model validation, impact studies | Universities, APHRC |
| Funders | Scale-up capital | MIT Solve, USAID, Gates Foundation |

---

## 11. Revenue Model (Sustainability)

The health risk platform is built on top of GidiNest's existing fintech model:

1. **Core Revenue (Existing):**
   - Interest margin on savings
   - Transaction fees
   - Partner commissions

2. **Health Platform Revenue (New):**
   - B2B licensing to health insurers
   - Government contracts for population health monitoring
   - NGO partnerships for program delivery
   - Premium "maternal health package" for users

---

## 12. Summary: Why This Works

| Traditional Approach | GidiNest Approach |
|---------------------|-------------------|
| Wait for missed appointments | Predict disruption from financial signals |
| Require clinical data | Use financial behavior as proxy |
| Reactive intervention | Proactive outreach |
| Health system silos | Embedded in daily financial life |
| One-time assessments | Continuous monitoring |
| Ignores economic factors | Financial health = healthcare access |

---

## Next Steps

1. **For MIT Solve submission:** Use this document to frame the technical approach
2. **For MVP:** Start with Phase 1 (Risk Scoring Engine) using existing data
3. **For pilots:** Partner with 1-2 health NGOs to test intervention workflows
4. **For validation:** Track outcomes to prove the model works

---

*Document created: January 2026*
*GidiNest - Where Financial Health Meets Maternal Health*
