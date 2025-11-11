"""
URL configuration for gidinest_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


admin.site.site_header = "Gidinest Internal Admin"
admin.site.site_title = "Gidinest Admin Portal"
admin.site.index_title = "Welcome to Gidinest Admin"


urlpatterns = [
    path('internal-admin/', admin.site.urls),

    # ==========================================
    # API DOCUMENTATION (Swagger/OpenAPI)
    # ==========================================
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ==========================================
    # V1 API - WEB APPLICATION (EXISTING - FROZEN)
    # ==========================================
    path("api/v1/account/", include("account.urls")),
    path("api/v1/onboarding/", include("onboarding.urls")),
    path('api/v1/savings/', include('savings.urls')),
    path('api/v1/wallet/', include('wallet.urls')),
    path('api/v1/community/', include('community.urls')),

    # ==========================================
    # V2 API - MOBILE APPLICATION (NEW)
    # ==========================================
    path("api/v2/auth/", include("onboarding.urls_v2")),
    path("api/v2/profile/", include("account.urls_v2")),
    path("api/v2/kyc/", include("account.urls_v2_kyc")),
    path("api/v2/dashboard/", include("dashboard.urls")),
    path("api/v2/wallet/", include("wallet.urls_v2")),
    path("api/v2/transactions/", include("transactions.urls")),
    path("api/v2/savings/", include("savings.urls_v2")),
    path("api/v2/community/", include("community.urls_v2")),
    path("api/v2/notifications/", include("notification.urls_v2")),
]
