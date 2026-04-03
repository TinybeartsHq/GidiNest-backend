# gifting/urls.py
from django.urls import path
from gifting.views import (
    CreateBabyFundAPIView,
    ListMyFundsAPIView,
    FundAnalyticsAPIView,
    UpdateBabyFundAPIView,
    DeactivateBabyFundAPIView,
    ViewFundPublicAPIView,
    InitializeGiftAPIView,
    GiftCallbackAPIView,
)

urlpatterns = [
    # Mother (fund owner) — auth required
    path('create', CreateBabyFundAPIView.as_view(), name='create-fund'),
    path('my-funds', ListMyFundsAPIView.as_view(), name='my-funds'),
    path('<str:token>/analytics', FundAnalyticsAPIView.as_view(), name='fund-analytics'),
    path('<str:token>/update', UpdateBabyFundAPIView.as_view(), name='update-fund'),
    path('<str:token>/deactivate', DeactivateBabyFundAPIView.as_view(), name='deactivate-fund'),

    # Gift sender (contributor) — public, no auth
    path('<str:token>/', ViewFundPublicAPIView.as_view(), name='view-fund'),
    path('<str:token>/gift', InitializeGiftAPIView.as_view(), name='initialize-gift'),
    path('<str:token>/success', GiftCallbackAPIView.as_view(), name='gift-callback'),
]
