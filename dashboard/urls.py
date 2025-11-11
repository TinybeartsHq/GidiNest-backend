# dashboard/urls.py
"""
V2 URLs for Mobile App - Dashboard
Unified dashboard endpoint that returns all necessary data in one request
"""

from django.urls import path
from .views import DashboardView

urlpatterns = [
    path('', DashboardView.as_view(), name='v2-dashboard'),
]
