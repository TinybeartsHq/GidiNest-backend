from django.urls import path
from .views import UserProfileView,UpdateBVNView

urlpatterns = [
    path('profile', UserProfileView.as_view(), name='user-profile'),
    path('bvn-update', UpdateBVNView.as_view(), name='update-bvn'),
]

