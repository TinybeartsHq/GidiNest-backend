# dashboard/views.py
"""
Dashboard Views for Mobile App V2 API
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class DashboardView(APIView):
    """
    Unified Dashboard API
    Returns all dashboard data in one optimized request

    TODO: Implement full logic
    - Get user details
    - Get wallet balance
    - Calculate quick stats
    - Get recent transactions (last 5)
    - Get active savings goals
    - Cache response in Redis (30 seconds)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # TODO: Implement actual dashboard logic
        return Response({
            "success": True,
            "data": {
                "user": {
                    "id": str(request.user.id),
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                    "is_verified": request.user.is_verified,
                },
                "wallet": {},
                "quick_stats": {},
                "recent_transactions": [],
                "savings_goals": []
            }
        }, status=status.HTTP_200_OK)
