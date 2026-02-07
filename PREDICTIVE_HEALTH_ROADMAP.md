# GidiNest Predictive Maternal Health Platform — Roadmap

## Vision
> GidiNest spots pregnant women who may not make it to a health facility for delivery — by tracking early warning signs like irregular saving or dropping engagement. This lets us offer help before it's too late.

---

## Phase 0: Foundation (Now — Week 2)
**Goal:** Prepare for MIT Solve submission + set up data infrastructure

### Tasks
| Task | Owner | Deadline |
|------|-------|----------|
| Finalize MIT Solve application narrative | | Week 1 |
| Document existing data fields available | | Week 1 |
| Define risk score formula (v1) | | Week 1 |
| Create basic SQL query to identify at-risk users | | Week 2 |
| Manual outreach to 10 at-risk users (proof of concept) | | Week 2 |

### Deliverables
- [ ] MIT Solve submission completed
- [ ] Risk scoring formula documented
- [ ] First "at-risk" user list generated manually
- [ ] 10 proof-of-concept calls made

---

## Phase 1: MVP Risk Engine (Week 3 — Week 6)
**Goal:** Automated risk scoring for all pregnant users

### Tasks
| Task | Owner | Deadline |
|------|-------|----------|
| Create `MaternalRiskScore` database model | Dev | Week 3 |
| Build risk calculation algorithm | Dev | Week 4 |
| Set up daily batch job to calculate scores | Dev | Week 4 |
| Build basic admin dashboard (at-risk list) | Dev | Week 5 |
| Test with 50 users | Team | Week 6 |

### Deliverables
- [ ] Risk scores calculated daily for all pregnant users
- [ ] Admin can view sorted list of at-risk mothers
- [ ] Risk factors visible (why is she flagged?)

### Success Metrics
- Risk scores generated for 100% of pregnant users
- Dashboard load time < 3 seconds
- Team can identify top 10 at-risk users in < 1 minute

---

## Phase 2: Alert & Intervention System (Week 7 — Week 10)
**Goal:** Automated alerts when risk increases

### Tasks
| Task | Owner | Deadline |
|------|-------|----------|
| Define alert triggers and thresholds | Product | Week 7 |
| Build alert queue system | Dev | Week 8 |
| Integrate SMS alerts (Cuoral/ZeptoMail) | Dev | Week 8 |
| Build escalation workflow (auto → manual → CHW) | Dev | Week 9 |
| Create intervention tracking (was she reached?) | Dev | Week 10 |

### Alert Triggers
```
Trigger 1: Score crosses 50 (Medium → High)
  → Send SMS: "Hi [Name], we noticed you haven't saved recently. Everything okay? Reply HELP if you need support."

Trigger 2: Score crosses 75 (High → Critical)
  → Phone call from GidiNest team within 24 hours

Trigger 3: No response to Trigger 2 for 72 hours
  → Flag for community health worker outreach

Trigger 4: Third trimester + Critical score
  → Immediate escalation to health partner
```

### Deliverables
- [ ] Automated SMS sent when risk increases
- [ ] Call list generated daily for team
- [ ] Escalation to CHW partner (if available)
- [ ] Intervention outcomes tracked

### Success Metrics
- 90% of high-risk users contacted within 48 hours
- 50% response rate to SMS outreach
- Intervention logged for every alert

---

## Phase 3: Outcome Tracking & Validation (Week 11 — Week 16)
**Goal:** Prove the model works

### Tasks
| Task | Owner | Deadline |
|------|-------|----------|
| Add birth outcome tracking (facility vs home) | Dev | Week 11 |
| In-app survey: "Where did you deliver?" | Dev | Week 12 |
| Collect outcomes for 100+ mothers | Team | Week 14 |
| Analyze: Do high-risk scores predict home delivery? | Data | Week 15 |
| Refine risk model based on findings | Dev | Week 16 |

### Data to Collect
```
Post-delivery survey:
1. Where did you give birth? (Health facility / Home / Other)
2. Did you have any challenges reaching the facility? (Y/N)
3. If yes, what was the main challenge? (Cost / Transport / Distance / Other)
```

### Deliverables
- [ ] Birth outcome data for 100+ users
- [ ] Correlation analysis: risk score vs actual outcome
- [ ] Model accuracy report (sensitivity, specificity)
- [ ] Refined risk weights based on real data

### Success Metrics
- High-risk mothers are 3x+ more likely to deliver outside facility
- Model achieves >70% sensitivity (catches most at-risk)
- False positive rate < 40%

---

## Phase 4: Health Partner Integration (Week 17 — Week 24)
**Goal:** Connect to community health workers and clinics

### Tasks
| Task | Owner | Deadline |
|------|-------|----------|
| Identify CHW partner organization | BD | Week 17 |
| Define referral workflow | Product | Week 18 |
| Build CHW portal (simple web view) | Dev | Week 20 |
| Pilot with 1 CHW organization | Team | Week 22 |
| Iterate based on feedback | Team | Week 24 |

### CHW Portal Features (Simple)
```
- List of referred mothers (sorted by risk)
- Mother's contact info + location
- Risk factors summary
- "Mark as contacted" button
- Outcome recording (reached / not reached / delivered safely)
```

### Deliverables
- [ ] Partnership with 1 CHW organization
- [ ] CHW portal live
- [ ] 50+ referrals made to CHWs
- [ ] Feedback collected, v2 planned

### Success Metrics
- CHW contacts 80% of referred mothers
- 70% of contacted mothers deliver in facility
- CHW satisfaction score > 4/5

---

## Phase 5: Scale & Extend (Month 7 — Month 12)
**Goal:** Expand to postnatal + immunisation, grow user base

### Extensions
| Extension | Description | Timeline |
|-----------|-------------|----------|
| Postnatal care continuity | Predict dropout from postnatal visits | Month 7-8 |
| Immunisation tracking | Predict missed vaccinations | Month 9-10 |
| Climate vulnerability layer | Integrate weather/disaster data | Month 10-11 |
| Multi-state expansion | Expand beyond initial geography | Month 11-12 |

### Deliverables
- [ ] Postnatal risk model live
- [ ] Immunisation reminder system live
- [ ] Climate alerts integrated
- [ ] 10,000+ mothers monitored

---

## Key Milestones Summary

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| MIT Solve submission | Week 1-2 | 🔲 |
| First risk scores generated | Week 4 | 🔲 |
| Admin dashboard live | Week 5 | 🔲 |
| First automated alert sent | Week 8 | 🔲 |
| 100 birth outcomes collected | Week 14 | 🔲 |
| Model validation complete | Week 16 | 🔲 |
| First CHW partnership live | Week 22 | 🔲 |
| 1,000 mothers monitored | Month 6 | 🔲 |
| Postnatal extension live | Month 8 | 🔲 |
| 10,000 mothers monitored | Month 12 | 🔲 |

---

## Resource Requirements

### Team
| Role | Responsibility | Existing/Needed |
|------|----------------|-----------------|
| Product Lead | Roadmap, prioritization, partnerships | Existing |
| Backend Developer | Risk engine, alerts, API | Existing |
| Frontend Developer | Dashboard, CHW portal | Existing/Part-time |
| Data Analyst | Model validation, refinement | Needed (Part-time) |
| Community Manager | User outreach, calls | Needed (Part-time) |
| BD/Partnerships | CHW orgs, health system | Existing |

### Budget (Estimated)
| Item | Monthly Cost | Notes |
|------|--------------|-------|
| SMS alerts (Cuoral) | ₦50,000 | ~500 SMS/month |
| Additional hosting | ₦20,000 | If needed |
| Part-time data analyst | ₦150,000 | 3 months |
| Community manager | ₦100,000 | For outreach calls |
| CHW incentives | ₦100,000 | Per-referral payments |
| **Total** | **₦420,000/month** | ~$280/month |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Users don't respond to outreach | Can't intervene | Test multiple channels (SMS, call, WhatsApp) |
| Can't collect birth outcomes | Can't validate model | Incentivize survey completion (₦500 airtime) |
| CHW partners unresponsive | No last-mile delivery | Start with 2-3 partners, choose most engaged |
| Model doesn't predict well | Credibility loss | Start with simple rules, refine with data |
| MIT Solve rejection | Funding gap | Apply to multiple grants simultaneously |

---

## Quick Wins (Do This Week)

1. **Write one SQL query** to find:
   - Pregnant users
   - Who haven't saved in 14+ days
   - AND haven't logged in for 7+ days
   - AND are in third trimester

2. **Call 5 of them** and ask:
   - "How are you doing?"
   - "Any challenges with your pregnancy?"
   - "Are you planning to deliver at a facility?"

3. **Document what you learn** — this becomes your proof of concept

---

## MIT Solve Submission Checklist

- [ ] Solution description (use narrative from earlier)
- [ ] Problem statement (maternal mortality + care access)
- [ ] Unique approach (financial signals as health proxy)
- [ ] Team information
- [ ] Traction/proof points (users, savings data, any outcomes)
- [ ] Roadmap (this document)
- [ ] Budget request
- [ ] Impact metrics (what you'll measure)
- [ ] Video pitch (if required)

---

## Next Steps

| Action | Who | By When |
|--------|-----|---------|
| Finalize MIT Solve application | | |
| Run first "at-risk" SQL query | | |
| Make 5 proof-of-concept calls | | |
| Design risk score database model | | |
| Identify 2-3 potential CHW partners | | |

---

*Last updated: January 2026*
