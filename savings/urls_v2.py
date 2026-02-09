# savings/urls_v2.py
"""
V2 URLs for Mobile App - Savings & Goals
Enhanced savings APIs with auto-save, categories, and comprehensive goal management
"""

from django.urls import path
from .views_v2 import (
    # Templates & Batch
    BatchCreateGoalsAPIView,
    GoalTemplatesAPIView,
    RecommendedGoalsAPIView,
    # CRUD
    GoalsListCreateAPIView,
    GoalDetailAPIView,
    # Operations
    GoalFundAPIView,
    GoalWithdrawAPIView,
    GoalTransactionsAPIView,
)

urlpatterns = [
    # ==========================================
    # GOALS CRUD
    # ==========================================
    path('goals', GoalsListCreateAPIView.as_view(), name='v2-goals-list'),  # GET, POST
    path('goals/<int:goal_id>', GoalDetailAPIView.as_view(), name='v2-goal-detail'),  # GET, PUT, DELETE

    # ==========================================
    # GOAL OPERATIONS
    # ==========================================
    path('goals/<int:goal_id>/fund', GoalFundAPIView.as_view(), name='v2-goal-fund'),  # POST
    path('goals/<int:goal_id>/withdraw', GoalWithdrawAPIView.as_view(), name='v2-goal-withdraw'),  # POST
    path('goals/<int:goal_id>/transactions', GoalTransactionsAPIView.as_view(), name='v2-goal-transactions'),  # GET

    # ==========================================
    # GOAL TEMPLATES & BATCH CREATION
    # ==========================================
    path('templates', GoalTemplatesAPIView.as_view(), name='v2-goal-templates'),  # GET
    path('templates/recommended', RecommendedGoalsAPIView.as_view(), name='v2-recommended-goals'),  # GET
    path('goals/batch-create', BatchCreateGoalsAPIView.as_view(), name='v2-batch-create-goals'),  # POST
]
