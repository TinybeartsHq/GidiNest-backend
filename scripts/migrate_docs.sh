#!/bin/bash

# Documentation Migration Script
# This script helps organize documentation files

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
ARCHIVE_DIR="$PROJECT_ROOT/docs_archive"

echo "📚 GidiNest Documentation Migration Script"
echo "==========================================="
echo ""

# Create directories
echo "Creating directory structure..."
mkdir -p "$DOCS_DIR"/{api,deployment,developer-setup}
mkdir -p "$ARCHIVE_DIR"

# Move API documentation (keep in codebase for now, but organized)
echo ""
echo "📄 Organizing API Documentation..."
mv "$PROJECT_ROOT/V1_API_DOCUMENTATION.md" "$DOCS_DIR/api/" 2>/dev/null || true
mv "$PROJECT_ROOT/V2_API_DOCUMENTATION.md" "$DOCS_DIR/api/" 2>/dev/null || true
mv "$PROJECT_ROOT/MOBILE_API_ENDPOINTS.md" "$DOCS_DIR/api/" 2>/dev/null || true
mv "$PROJECT_ROOT/V2_API_AVAILABILITY.md" "$DOCS_DIR/api/" 2>/dev/null || true

# Move deployment docs (keep in codebase - useful for developers)
echo ""
echo "🚀 Organizing Deployment Documentation..."
mv "$PROJECT_ROOT/DEPLOYMENT_GUIDE.md" "$DOCS_DIR/deployment/" 2>/dev/null || true
mv "$PROJECT_ROOT/PRE_DEPLOYMENT_CHECKLIST.md" "$DOCS_DIR/deployment/" 2>/dev/null || true

# Move developer setup docs
echo ""
echo "⚙️  Organizing Developer Setup Documentation..."
mv "$PROJECT_ROOT/MOBILE_APP_ENV_CONFIG.md" "$DOCS_DIR/developer-setup/" 2>/dev/null || true

# Archive files that should move to external platform
echo ""
echo "📦 Archiving files for external platform migration..."
mv "$PROJECT_ROOT/EMBEDLY_BANKS_API_ISSUE.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/PERFORMANCE_ISSUES_AND_FIXES.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/WEBHOOK_DIAGNOSTICS.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/URGENT_EMBEDLY_PAYOUT_API_FAILURE.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/MOBILE_APP_CONNECTION_FIXED.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/CHECK_LOGS.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/RESTART_REQUIRED.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/V2_API_CHECKLIST.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/V2_IMPLEMENTATION_REVIEW.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/V2_ONBOARDING_IMPLEMENTATION_PROGRESS.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/PHASE1_URL_STRUCTURE_COMPLETE.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/GAP_ANALYSIS_AND_ACTION_PLAN.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/API_VERSIONING_STRATEGY.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/WEB_MOBILE_COMPATIBILITY_STRATEGY.md" "$ARCHIVE_DIR/" 2>/dev/null || true
mv "$PROJECT_ROOT/SHARED_DATABASE_WARNING.md" "$ARCHIVE_DIR/" 2>/dev/null || true

# Create README in docs folder
cat > "$DOCS_DIR/README.md" << 'EOF'
# GidiNest Backend Documentation

This folder contains essential developer documentation for the GidiNest backend.

## 📁 Structure

- **api/** - API documentation and references
- **deployment/** - Deployment guides and checklists
- **developer-setup/** - Environment configuration and setup guides

## 📚 Additional Documentation

For comprehensive documentation including:
- Runbooks and troubleshooting guides
- Incident logs and post-mortems
- Architecture decision records (ADRs)
- Project tracking and implementation progress

Please refer to our [Notion/Confluence/Wiki] documentation portal.

## 🔗 Quick Links

- API Documentation: [docs/api/](api/)
- Deployment Guide: [docs/deployment/DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)
- Developer Setup: [docs/developer-setup/](developer-setup/)
EOF

echo ""
echo "✅ Migration complete!"
echo ""
echo "📋 Summary:"
echo "   - Developer docs organized in: $DOCS_DIR"
echo "   - Files ready for external platform: $ARCHIVE_DIR"
echo ""
echo "📝 Next steps:"
echo "   1. Review files in $ARCHIVE_DIR"
echo "   2. Upload archived files to your documentation platform (Notion/Confluence)"
echo "   3. Update the README.md in docs/ with your documentation platform URL"
echo "   4. Commit the changes to git"
echo ""


