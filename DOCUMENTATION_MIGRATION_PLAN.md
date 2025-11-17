# Documentation Migration Plan

## Current Documentation Files (22 files)

### Category 1: API Documentation (Should stay in codebase or separate API docs repo)
- `V1_API_DOCUMENTATION.md` - API reference
- `V2_API_DOCUMENTATION.md` - API reference  
- `MOBILE_API_ENDPOINTS.md` - API reference
- `V2_API_AVAILABILITY.md` - API status/reference

**Recommendation:** Move to separate `docs/api/` folder OR dedicated API documentation site (Swagger/OpenAPI)

---

### Category 2: Developer Setup & Deployment (Can stay in codebase)
- `DEPLOYMENT_GUIDE.md` - Developer reference
- `PRE_DEPLOYMENT_CHECKLIST.md` - Developer reference
- `MOBILE_APP_ENV_CONFIG.md` - Developer reference

**Recommendation:** Keep in `docs/` folder in codebase (useful for developers)

---

### Category 3: Technical Issues & Troubleshooting (Move to wiki/knowledge base)
- `EMBEDLY_BANKS_API_ISSUE.md` - Incident documentation
- `PERFORMANCE_ISSUES_AND_FIXES.md` - Incident/post-mortem
- `WEBHOOK_DIAGNOSTICS.md` - Troubleshooting guide
- `URGENT_EMBEDLY_PAYOUT_API_FAILURE.md` - Incident documentation
- `MOBILE_APP_CONNECTION_FIXED.md` - Incident resolution
- `CHECK_LOGS.md` - Runbook/troubleshooting
- `RESTART_REQUIRED.md` - Operational notice

**Recommendation:** Move to Confluence/Notion/wiki as "Runbooks" or "Incident Logs"

---

### Category 4: Implementation Progress & Reviews (Move to project management)
- `V2_API_CHECKLIST.md` - Project tracking
- `V2_IMPLEMENTATION_REVIEW.md` - Project review
- `V2_ONBOARDING_IMPLEMENTATION_PROGRESS.md` - Project tracking
- `PHASE1_URL_STRUCTURE_COMPLETE.md` - Project milestone
- `GAP_ANALYSIS_AND_ACTION_PLAN.md` - Strategic planning

**Recommendation:** Move to project management tool (Jira, Linear, GitHub Projects) or Confluence

---

### Category 5: Architecture & Strategy (Move to company wiki)
- `API_VERSIONING_STRATEGY.md` - Architecture decision
- `WEB_MOBILE_COMPATIBILITY_STRATEGY.md` - Architecture decision
- `SHARED_DATABASE_WARNING.md` - Architecture notice

**Recommendation:** Move to Confluence/Notion as "Architecture Decision Records (ADRs)"

---

## Recommended Structure

### Option A: Separate Documentation Repository (Recommended)
```
GidiNest-docs/
├── README.md
├── api/
│   ├── v1/
│   ├── v2/
│   └── mobile/
├── deployment/
│   ├── deployment-guide.md
│   └── pre-deployment-checklist.md
├── runbooks/
│   ├── troubleshooting/
│   └── incidents/
├── architecture/
│   ├── adr/
│   └── strategies/
└── developer-setup/
    └── environment-config.md
```

### Option B: Documentation Platform (Confluence/Notion)
- **API Documentation** → Confluence Space: "API Reference"
- **Runbooks** → Confluence Space: "Operations"
- **Architecture** → Confluence Space: "Architecture & Design"
- **Project Tracking** → Jira/GitHub Projects

### Option C: Hybrid (Recommended for startups)
- **Keep in codebase:** `docs/` folder with essential developer docs
- **Move to Notion/Confluence:** Strategic docs, runbooks, incident logs
- **Use GitHub Wiki:** Quick reference guides

---

## Migration Steps

1. **Set up documentation platform** (Confluence/Notion/GitBook)
2. **Create folder structure** matching categories above
3. **Migrate files** one category at a time
4. **Update references** in code/comments
5. **Add README** in codebase pointing to new locations
6. **Archive old files** (keep for 30 days, then delete)

---

## Quick Win: Immediate Action

Create a `docs/` folder in codebase and move only essential developer docs there:

```bash
mkdir docs
mv DEPLOYMENT_GUIDE.md docs/
mv PRE_DEPLOYMENT_CHECKLIST.md docs/
mv MOBILE_APP_ENV_CONFIG.md docs/
```

Then move everything else to your chosen documentation platform.




