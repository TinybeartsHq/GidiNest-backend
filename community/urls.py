# community/urls.py
from django.urls import path
from .views import (
    CommunityPostListCreateAPIView,
    CommunityPostDetailAPIView,
    CommunityCommentListCreateAPIView,
    CommunityCommentDetailAPIView
)

urlpatterns = [
    # Posts
    path('posts', CommunityPostListCreateAPIView.as_view(), name='community_posts_list_create'),
    path('posts/<int:pk>', CommunityPostDetailAPIView.as_view(), name='community_post_detail'),

    # Comments
    path('posts/<int:post_id>/comments', CommunityCommentListCreateAPIView.as_view(), name='community_comments_list_create'),
    path('comments/<int:pk>', CommunityCommentDetailAPIView.as_view(), name='community_comment_detail'),
]