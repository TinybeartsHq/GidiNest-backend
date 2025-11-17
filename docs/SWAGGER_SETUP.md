# Swagger/OpenAPI Documentation Setup

## ✅ Current Status

Swagger is **already configured** and ready to use! Your API documentation is automatically generated from your Django REST Framework code.

## 🔗 Access Points

### Local Development
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **OpenAPI Schema (JSON):** http://localhost:8000/api/schema/
- **OpenAPI Schema (YAML):** http://localhost:8000/api/schema/?format=openapi

### Production
- **Swagger UI:** https://api.gidinest.com/api/docs/
- **ReDoc:** https://api.gidinest.com/api/redoc/
- **OpenAPI Schema:** https://api.gidinest.com/api/schema/

## 🎯 Features

Your Swagger setup includes:

- ✅ **Interactive API Testing** - Test endpoints directly from the browser
- ✅ **JWT Authentication** - Supports Bearer token authentication
- ✅ **Auto-generated** - Always up-to-date with your code
- ✅ **Request/Response Examples** - See expected formats
- ✅ **Schema Validation** - Understand data structures
- ✅ **Deep Linking** - Direct links to specific endpoints
- ✅ **Filtering** - Search and filter endpoints
- ✅ **Persistent Authorization** - Saves your auth tokens

## 📝 Configuration

Swagger is configured in `gidinest_backend/settings.py`:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'GidiNest API',
    'DESCRIPTION': '...',
    'VERSION': '2.0.0',
    'SERVERS': [
        {'url': 'https://api.gidinest.com', 'description': 'Production Server'},
        {'url': 'http://localhost:8000', 'description': 'Local Development Server'},
    ],
    # ... more settings
}
```

## 🔐 Authentication

To use authenticated endpoints in Swagger:

1. Click the **"Authorize"** button (top right)
2. Enter: `Bearer <your_jwt_token>`
3. Click **"Authorize"**
4. Your token will be saved for the session

## 📚 Adding Documentation to Your Views

### Using DRF ViewSets/Views

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

class MyViewSet(viewsets.ModelViewSet):
    @extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's profile information",
        tags=['V2 - Profile'],
        responses={200: UserProfileSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
```

### Using Function-Based Views

```python
from drf_spectacular.utils import extend_schema

@extend_schema(
    summary="Create wallet",
    description="Create a new wallet for the authenticated user",
    tags=['V2 - Wallet'],
    request=WalletCreateSerializer,
    responses={201: WalletSerializer}
)
@api_view(['POST'])
def create_wallet(request):
    # Your view logic
    pass
```

## 🏷️ Tags

Your API is organized with tags:
- `V1 - Authentication` - Web app authentication
- `V1 - Account` - Web app account management
- `V1 - Wallet` - Web app wallet operations
- `V2 - Auth` - Mobile app authentication
- `V2 - Profile` - Mobile app profile management
- And more...

## 🚀 Best Practices

1. **Always document your endpoints** - Use `@extend_schema` decorator
2. **Add descriptions** - Help developers understand your API
3. **Use proper tags** - Organize endpoints logically
4. **Include examples** - Show request/response examples
5. **Keep it updated** - Swagger auto-generates, but add descriptions

## 📖 Resources

- [DRF Spectacular Documentation](https://drf-spectacular.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)

## 🔄 Migration from Markdown Docs

The markdown API documentation files in `docs/api/` are now **legacy**. 

**For the most current and accurate API documentation, always refer to Swagger UI** at `/api/docs/`.

The markdown files are kept for reference but may become outdated as the API evolves.




