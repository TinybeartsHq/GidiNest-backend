from django.urls import path
from .views import (
    UserProfileView,
    UpdateBVNView,
    UpdateNINView,
    AccountTierInfoView,
    VerificationStatusView,
    SyncEmbedlyVerificationView
)

urlpatterns = [
    path('profile', UserProfileView.as_view(), name='user-profile'),
    path('bvn-update', UpdateBVNView.as_view(), name='update-bvn'),
    path('nin-update', UpdateNINView.as_view(), name='update-nin'),
    path('tier-info', AccountTierInfoView.as_view(), name='account-tier-info'),
    path('verification-status', VerificationStatusView.as_view(), name='verification-status'),
    path('sync-embedly', SyncEmbedlyVerificationView.as_view(), name='sync-embedly-verification'),
]

