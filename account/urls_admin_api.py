# account/urls_admin_api.py
"""
Admin API URLs for internal operations
All endpoints require staff/admin authentication
"""

from django.urls import path
from account.admin_api_views import AdminWalletFixView

urlpatterns = [
    # ==========================================
    # ADMIN WALLET MANAGEMENT
    # ==========================================
    # GET: List users with wallet issues
    # POST: Fix wallet issues (bulk or single user)
    path('wallet/fix', AdminWalletFixView.as_view(), name='admin-wallet-fix'),
]
