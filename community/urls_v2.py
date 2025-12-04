# community/urls_v2.py
"""
V2 URLs for Mobile App - Community
Enhanced community features with groups, moderation, challenges, and leaderboard
"""

from django.urls import path
from .views import (
    # Groups
    CommunityGroupListCreateAPIView,
    CommunityGroupDetailAPIView,
    GroupJoinLeaveAPIView,

    # Posts
    CommunityPostListCreateAPIView,
    CommunityPostDetailAPIView,
    PostLikeToggleAPIView,

    # Comments
    CommunityCommentListCreateAPIView,
    CommunityCommentDetailAPIView,

    # Moderation
    PostModerationListAPIView,
    PostApproveRejectAPIView,
    CommentModerationListAPIView,
    CommentApproveRejectAPIView,

    # Challenges
    SavingsChallengeListCreateAPIView,
    ChallengeJoinAPIView,
    ChallengeUpdateProgressAPIView,

    # Leaderboard & Stats
    GroupLeaderboardAPIView,
    CommunityStatsAPIView,
)

urlpatterns = [
    # ==========================================
    # COMMUNITY STATS
    # ==========================================
    path('stats', CommunityStatsAPIView.as_view(), name='v2-community-stats'),

    # ==========================================
    # GROUPS
    # ==========================================
    path('groups', CommunityGroupListCreateAPIView.as_view(), name='v2-groups-list'),
    path('groups/<int:pk>', CommunityGroupDetailAPIView.as_view(), name='v2-group-detail'),
    path('groups/<int:pk>/join', GroupJoinLeaveAPIView.as_view(), name='v2-group-join-leave'),

    # ==========================================
    # POSTS
    # ==========================================
    path('posts', CommunityPostListCreateAPIView.as_view(), name='v2-posts-list'),
    path('posts/<int:pk>', CommunityPostDetailAPIView.as_view(), name='v2-post-detail'),
    path('posts/<int:pk>/like', PostLikeToggleAPIView.as_view(), name='v2-post-like'),

    # ==========================================
    # COMMENTS
    # ==========================================
    path('posts/<int:post_id>/comments', CommunityCommentListCreateAPIView.as_view(), name='v2-comments-list'),
    path('comments/<int:pk>', CommunityCommentDetailAPIView.as_view(), name='v2-comment-detail'),

    # ==========================================
    # MODERATION (Admin/Moderator only)
    # ==========================================
    path('moderation/posts', PostModerationListAPIView.as_view(), name='v2-moderation-posts'),
    path('moderation/posts/<int:pk>/review', PostApproveRejectAPIView.as_view(), name='v2-moderation-post-review'),
    path('moderation/comments', CommentModerationListAPIView.as_view(), name='v2-moderation-comments'),
    path('moderation/comments/<int:pk>/review', CommentApproveRejectAPIView.as_view(), name='v2-moderation-comment-review'),

    # ==========================================
    # CHALLENGES
    # ==========================================
    path('challenges', SavingsChallengeListCreateAPIView.as_view(), name='v2-challenges-list'),
    path('challenges/<int:pk>/join', ChallengeJoinAPIView.as_view(), name='v2-challenge-join'),
    path('challenge-participations/<int:pk>/update-progress', ChallengeUpdateProgressAPIView.as_view(), name='v2-challenge-update-progress'),

    # ==========================================
    # LEADERBOARD
    # ==========================================
    path('groups/<int:group_id>/leaderboard', GroupLeaderboardAPIView.as_view(), name='v2-group-leaderboard'),
]
