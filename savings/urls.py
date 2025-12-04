# savings/urls.py
from django.urls import path
from .views import SavingsGoalAPIView, SavingsGoalContributeWithdrawAPIView, SpecificSavingsGoalHistoryAPIView, UserAllSavingsHistoryAPIView, SavingsDashboardAnalyticsAPIView

urlpatterns = [
    path('goals/', SavingsGoalAPIView.as_view(), name='savings_goals_list_create'),
    path('goals/<int:goal_id>/', SavingsGoalAPIView.as_view(), name='delete-savings-goal'),

    path('goals/contribute-withdraw/', SavingsGoalContributeWithdrawAPIView.as_view(), name='savings_goal_contribute_withdraw'),
    path('history/all/', UserAllSavingsHistoryAPIView.as_view(), name='all_savings_history'),
    path('history/<uuid:goal_id>/', SpecificSavingsGoalHistoryAPIView.as_view(), name='specific_savings_history'),

    path('dashboard-analytics/', SavingsDashboardAnalyticsAPIView.as_view(), name='savings_dashboard_analytics'),
]