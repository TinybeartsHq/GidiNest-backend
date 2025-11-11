# transactions/urls.py
"""
V2 URLs for Mobile App - Transactions
Comprehensive transaction history with filtering and detailed views
"""

from django.urls import path
from .views import TransactionListView, TransactionDetailView

urlpatterns = [
    path('', TransactionListView.as_view(), name='v2-transactions-list'),
    path('<uuid:transaction_id>', TransactionDetailView.as_view(), name='v2-transaction-detail'),
]
