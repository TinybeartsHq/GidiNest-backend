# GidiNest Backend Documentation

This folder contains essential developer documentation for the GidiNest backend.

## 🚀 Getting Started

**New to the API?** Start here:
- **[API Guide](API_GUIDE.md)** - Choose the right API version for your platform
- **[Frontend Quick Start](frontend/QUICK_START.md)** - For web developers
- **[Mobile Quick Start](mobile/QUICK_START.md)** - For mobile developers

## 📁 Structure

- **[API_GUIDE.md](API_GUIDE.md)** - Main API guide (start here!)
- **api/** - API documentation and references (legacy markdown docs)
- **frontend/** - Frontend developer guides (V1 API)
- **mobile/** - Mobile developer guides (V2 API)
- **deployment/** - Deployment guides and checklists
- **developer-setup/** - Environment configuration and setup guides

## 🔗 Interactive API Documentation (Swagger/OpenAPI)

**Live API Documentation is available via Swagger UI:**

- **Swagger UI:** `http://localhost:8000/api/docs/` (or your domain + `/api/docs/`)
- **ReDoc:** `http://localhost:8000/api/redoc/` (alternative documentation view)
- **OpenAPI Schema:** `http://localhost:8000/api/schema/` (JSON/YAML schema)

The Swagger documentation is **auto-generated** from your Django REST Framework code and is always up-to-date with your API endpoints.

### Features:
- ✅ Interactive API testing
- ✅ Authentication support (JWT Bearer tokens)
- ✅ Request/Response examples
- ✅ Schema validation
- ✅ Try it out functionality

> **Note:** The markdown files in `api/` are legacy documentation. For the most current API documentation, use Swagger UI.

## 📚 Additional Documentation

For comprehensive documentation including:
- Runbooks and troubleshooting guides
- Incident logs and post-mortems
- Architecture decision records (ADRs)
- Project tracking and implementation progress

Please refer to our [Notion/Confluence/Wiki] documentation portal.

## 🔗 Quick Links

- **Interactive API Docs:** [Swagger UI](/api/docs/) | [ReDoc](/api/redoc/)
- **Legacy API Docs:** [docs/api/](api/)
- **Deployment Guide:** [docs/deployment/DEPLOYMENT_GUIDE.md](deployment/DEPLOYMENT_GUIDE.md)
- **Developer Setup:** [docs/developer-setup/](developer-setup/)
