# community/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from core.helpers.response import success_response, validation_error_response, error_response
from .models import (
    CommunityGroup, GroupMembership, CommunityPost, CommunityComment,
    PostLike, SavingsChallenge, ChallengeParticipation, GroupLeaderboard
)
from .serializers import (
    CommunityGroupListSerializer, CommunityGroupDetailSerializer,
    GroupMembershipSerializer, CommunityPostSerializer, CommunityPostDetailedSerializer,
    CommunityCommentSerializer, PostLikeSerializer, SavingsChallengeSerializer,
    ChallengeParticipationSerializer, GroupLeaderboardSerializer,
    PostModerationSerializer, CommentModerationSerializer
)
from .permissions import (
    IsAuthorOrReadOnly, IsGroupMemberOrReadOnly, IsGroupAdminOrModerator,
    CanModerateContent
)

# Notification helpers
try:
    from notification.helper.notifications import (
        notify_post_liked,
        notify_post_commented,
        notify_challenge_completed,
        create_notification
    )
    NOTIFICATIONS_AVAILABLE = True
except (ImportError, Exception):
    NOTIFICATIONS_AVAILABLE = False
    def notify_post_liked(*args, **kwargs): pass
    def notify_post_commented(*args, **kwargs): pass
    def notify_challenge_completed(*args, **kwargs): pass
    def create_notification(*args, **kwargs): pass


# ==========================================
# COMMUNITY GROUPS
# ==========================================

class CommunityGroupListCreateAPIView(APIView):
    """
    List all community groups or create a new one.
    GET: List all groups (with optional filtering)
    POST: Create a new group
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        groups = CommunityGroup.objects.filter(is_active=True)

        # Filter by category
        category = request.query_params.get('category')
        if category:
            groups = groups.filter(category=category)

        # Filter by badge
        badge = request.query_params.get('badge')
        if badge:
            groups = groups.filter(badge=badge)

        # Search by name
        search = request.query_params.get('search')
        if search:
            groups = groups.filter(Q(name__icontains=search) | Q(description__icontains=search))

        serializer = CommunityGroupListSerializer(groups, many=True, context={'request': request})
        return success_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CommunityGroupListSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Create the group and make the creator an admin
            with transaction.atomic():
                group = serializer.save(created_by=request.user)
                GroupMembership.objects.create(
                    group=group,
                    user=request.user,
                    role='admin',
                    is_active=True
                )
            return success_response(
                message="Community group created successfully.",
                data=CommunityGroupDetailSerializer(group, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)


class CommunityGroupDetailAPIView(APIView):
    """
    Retrieve, update, or delete a community group.
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        group = get_object_or_404(CommunityGroup, pk=pk, is_active=True)

        # Check if user can view private groups
        if group.privacy == 'private':
            if not group.memberships.filter(user=request.user, is_active=True).exists():
                return None

        return group

    def get(self, request, pk, *args, **kwargs):
        group = self.get_object(pk, request)
        if not group:
            return error_response(message="Group not found or you don't have access.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = CommunityGroupDetailSerializer(group, context={'request': request})
        return success_response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        group = self.get_object(pk, request)
        if not group:
            return error_response(message="Group not found or you don't have access.", status_code=status.HTTP_404_NOT_FOUND)

        # Check if user is admin
        membership = group.memberships.filter(user=request.user, is_active=True).first()
        if not membership or membership.role != 'admin':
            return error_response(message="Only group admins can update the group.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = CommunityGroupDetailSerializer(group, data=request.data, partial=False, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success_response(message="Group updated successfully.", data=serializer.data)
        return validation_error_response(serializer.errors)

    def patch(self, request, pk, *args, **kwargs):
        group = self.get_object(pk, request)
        if not group:
            return error_response(message="Group not found or you don't have access.", status_code=status.HTTP_404_NOT_FOUND)

        # Check if user is admin
        membership = group.memberships.filter(user=request.user, is_active=True).first()
        if not membership or membership.role != 'admin':
            return error_response(message="Only group admins can update the group.", status_code=status.HTTP_403_FORBIDDEN)

        serializer = CommunityGroupDetailSerializer(group, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success_response(message="Group updated successfully.", data=serializer.data)
        return validation_error_response(serializer.errors)

    def delete(self, request, pk, *args, **kwargs):
        group = self.get_object(pk, request)
        if not group:
            return error_response(message="Group not found or you don't have access.", status_code=status.HTTP_404_NOT_FOUND)

        # Check if user is admin
        membership = group.memberships.filter(user=request.user, is_active=True).first()
        if not membership or membership.role != 'admin':
            return error_response(message="Only group admins can delete the group.", status_code=status.HTTP_403_FORBIDDEN)

        group.is_active = False
        group.save()
        return success_response(message="Group deleted successfully.")


class GroupJoinLeaveAPIView(APIView):
    """
    Join or leave a community group.
    POST: Join a group
    DELETE: Leave a group
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        group = get_object_or_404(CommunityGroup, pk=pk, is_active=True)

        # Check if already a member
        existing = GroupMembership.objects.filter(group=group, user=request.user).first()
        if existing and existing.is_active:
            return error_response(message="You are already a member of this group.", status_code=status.HTTP_400_BAD_REQUEST)

        # Create or reactivate membership
        if existing:
            existing.is_active = True
            existing.role = 'member'
            existing.save()
            membership = existing
        else:
            membership = GroupMembership.objects.create(
                group=group,
                user=request.user,
                role='member'
            )

        # Send notification
        try:
            create_notification(
                user=request.user,
                title=f"Joined {group.name}",
                message=f"You've successfully joined the {group.name} community group",
                notification_type='group_joined',
                data={'group_name': group.name, 'group_id': str(group.id)},
                action_url=f'/community/groups/{group.id}',
                send_push=False  # Don't send push for group join
            )
        except Exception:
            pass  # Don't fail if notification fails

        return success_response(
            message="Successfully joined the group.",
            data=GroupMembershipSerializer(membership).data
        )

    def delete(self, request, pk, *args, **kwargs):
        group = get_object_or_404(CommunityGroup, pk=pk, is_active=True)

        membership = GroupMembership.objects.filter(group=group, user=request.user, is_active=True).first()
        if not membership:
            return error_response(message="You are not a member of this group.", status_code=status.HTTP_400_BAD_REQUEST)

        # Don't allow the last admin to leave
        if membership.role == 'admin':
            admin_count = group.memberships.filter(role='admin', is_active=True).count()
            if admin_count <= 1:
                return error_response(
                    message="You are the last admin. Please assign another admin before leaving.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        membership.is_active = False
        membership.save()
        return success_response(message="Successfully left the group.")


# ==========================================
# POSTS
# ==========================================

class CommunityPostListCreateAPIView(APIView):
    """
    List posts or create a new post.
    GET: List posts (optionally filtered by group)
    POST: Create a new post (goes to pending status)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Only show approved posts to regular users
        posts = CommunityPost.objects.filter(status='approved')

        # Filter by group
        group_id = request.query_params.get('group')
        if group_id:
            posts = posts.filter(group_id=group_id)

        # Filter by user's groups
        my_groups = request.query_params.get('my_groups')
        if my_groups == 'true':
            user_group_ids = GroupMembership.objects.filter(
                user=request.user,
                is_active=True
            ).values_list('group_id', flat=True)
            posts = posts.filter(group_id__in=user_group_ids)

        serializer = CommunityPostSerializer(posts, many=True, context={'request': request})
        return success_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CommunityPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Check if user is member of the group
            group_id = serializer.validated_data.get('group')
            if group_id:
                membership = GroupMembership.objects.filter(
                    group=group_id,
                    user=request.user,
                    is_active=True
                ).first()
                if not membership:
                    return error_response(
                        message="You must be a member of the group to post.",
                        status_code=status.HTTP_403_FORBIDDEN
                    )

            # Save post with pending status
            post = serializer.save(author=request.user, status='pending')
            return success_response(
                message="Post created and submitted for review.",
                data=CommunityPostSerializer(post, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)


class CommunityPostDetailAPIView(APIView):
    """
    Retrieve, update, or delete a specific post.
    """
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_object(self, pk):
        obj = get_object_or_404(CommunityPost, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)

        # Only show approved posts unless user is author or moderator
        if post.status != 'approved' and post.author != request.user:
            if post.group:
                membership = post.group.memberships.filter(user=request.user, is_active=True).first()
                if not membership or membership.role not in ['admin', 'moderator']:
                    return error_response(message="Post not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Increment view count
        post.views_count += 1
        post.save(update_fields=['views_count'])

        serializer = CommunityPostDetailedSerializer(post, context={'request': request})
        return success_response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        serializer = CommunityPostDetailedSerializer(post, data=request.data, partial=False, context={'request': request})
        if serializer.is_valid():
            # Reset to pending status after edit
            updated_post = serializer.save(status='pending')
            return success_response(
                message="Post updated and resubmitted for review.",
                data=CommunityPostDetailedSerializer(updated_post, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)

    def patch(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        serializer = CommunityPostDetailedSerializer(post, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            # Reset to pending status after edit
            updated_post = serializer.save(status='pending')
            return success_response(
                message="Post updated and resubmitted for review.",
                data=CommunityPostDetailedSerializer(updated_post, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)

    def delete(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        post.delete()
        return success_response(message="Post deleted successfully.")


class PostLikeToggleAPIView(APIView):
    """
    Toggle like on a post.
    POST: Like/Unlike a post
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(CommunityPost, pk=pk, status='approved')

        # Check if already liked
        existing_like = PostLike.objects.filter(post=post, user=request.user).first()

        if existing_like:
            # Unlike
            existing_like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            post.save(update_fields=['likes_count'])
            return success_response(message="Post unliked.", data={'is_liked': False, 'likes_count': post.likes_count})
        else:
            # Like
            PostLike.objects.create(post=post, user=request.user)
            post.likes_count += 1
            post.save(update_fields=['likes_count'])

            # Send notification to post author (don't notify if user likes their own post)
            if post.author != request.user:
                try:
                    notify_post_liked(
                        user=post.author,
                        liker_name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email,
                        post_id=post.id
                    )
                except Exception:
                    pass  # Don't fail if notification fails

            return success_response(message="Post liked.", data={'is_liked': True, 'likes_count': post.likes_count})


# ==========================================
# COMMENTS
# ==========================================

class CommunityCommentListCreateAPIView(APIView):
    """
    List comments for a post or create a new comment.
    GET: List approved comments for a post
    POST: Create a new comment (goes to pending status)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(CommunityPost, pk=post_id, status='approved')
        # Only show approved comments
        comments = post.comments.filter(status='approved')
        serializer = CommunityCommentSerializer(comments, many=True, context={'request': request})
        return success_response(serializer.data)

    def post(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(CommunityPost, pk=post_id, status='approved')

        serializer = CommunityCommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Save comment with pending status
            comment = serializer.save(author=request.user, post=post, status='pending')
            return success_response(
                message="Comment created and submitted for review.",
                data=CommunityCommentSerializer(comment, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)


class CommunityCommentDetailAPIView(APIView):
    """
    Retrieve, update, or delete a specific comment.
    """
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_object(self, pk):
        obj = get_object_or_404(CommunityComment, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment, context={'request': request})
        return success_response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment, data=request.data, partial=False, context={'request': request})
        if serializer.is_valid():
            # Reset to pending after edit
            updated_comment = serializer.save(status='pending')
            return success_response(
                message="Comment updated and resubmitted for review.",
                data=CommunityCommentSerializer(updated_comment, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)

    def patch(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            # Reset to pending after edit
            updated_comment = serializer.save(status='pending')
            return success_response(
                message="Comment updated and resubmitted for review.",
                data=CommunityCommentSerializer(updated_comment, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)

    def delete(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        post = comment.post
        comment.delete()
        # Update comment count
        post.comments_count = max(0, post.comments_count - 1)
        post.save(update_fields=['comments_count'])
        return success_response(message="Comment deleted successfully.")


# ==========================================
# MODERATION
# ==========================================

class PostModerationListAPIView(APIView):
    """
    List all pending posts for moderation.
    """
    permission_classes = [IsAuthenticated, CanModerateContent]

    def get(self, request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            # Staff can see all pending posts
            posts = CommunityPost.objects.filter(status='pending')
        else:
            # Group admins/moderators can only see their groups' pending posts
            user_admin_groups = GroupMembership.objects.filter(
                user=request.user,
                role__in=['admin', 'moderator'],
                is_active=True
            ).values_list('group_id', flat=True)
            posts = CommunityPost.objects.filter(group_id__in=user_admin_groups, status='pending')

        serializer = PostModerationSerializer(posts, many=True, context={'request': request})
        return success_response(serializer.data)


class PostApproveRejectAPIView(APIView):
    """
    Approve or reject a post.
    POST: Approve or reject with action parameter
    """
    permission_classes = [IsAuthenticated, CanModerateContent]

    def post(self, request, pk, *args, **kwargs):
        post = get_object_or_404(CommunityPost, pk=pk)

        # Check permission
        self.check_object_permissions(request, post)

        action = request.data.get('action')  # 'approve' or 'reject'
        rejection_reason = request.data.get('rejection_reason', '')

        if action == 'approve':
            post.status = 'approved'
            post.reviewed_by = request.user
            post.reviewed_at = timezone.now()
            post.save()
            return success_response(message="Post approved successfully.", data=PostModerationSerializer(post).data)

        elif action == 'reject':
            post.status = 'rejected'
            post.reviewed_by = request.user
            post.reviewed_at = timezone.now()
            post.rejection_reason = rejection_reason
            post.save()
            return success_response(message="Post rejected.", data=PostModerationSerializer(post).data)

        return validation_error_response({"action": "Invalid action. Use 'approve' or 'reject'."})


class CommentModerationListAPIView(APIView):
    """
    List all pending comments for moderation.
    """
    permission_classes = [IsAuthenticated, CanModerateContent]

    def get(self, request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            # Staff can see all pending comments
            comments = CommunityComment.objects.filter(status='pending')
        else:
            # Group admins/moderators can only see their groups' pending comments
            user_admin_groups = GroupMembership.objects.filter(
                user=request.user,
                role__in=['admin', 'moderator'],
                is_active=True
            ).values_list('group_id', flat=True)
            comments = CommunityComment.objects.filter(post__group_id__in=user_admin_groups, status='pending')

        serializer = CommentModerationSerializer(comments, many=True, context={'request': request})
        return success_response(serializer.data)


class CommentApproveRejectAPIView(APIView):
    """
    Approve or reject a comment.
    POST: Approve or reject with action parameter
    """
    permission_classes = [IsAuthenticated, CanModerateContent]

    def post(self, request, pk, *args, **kwargs):
        comment = get_object_or_404(CommunityComment, pk=pk)

        # Check permission
        self.check_object_permissions(request, comment)

        action = request.data.get('action')  # 'approve' or 'reject'
        rejection_reason = request.data.get('rejection_reason', '')

        if action == 'approve':
            comment.status = 'approved'
            comment.reviewed_by = request.user
            comment.reviewed_at = timezone.now()
            comment.save()
            # Update post comment count
            comment.post.comments_count += 1
            comment.post.save(update_fields=['comments_count'])

            # Send notification to post author (don't notify if commenting on own post)
            if comment.post.author != comment.author:
                try:
                    commenter_name = f"{comment.author.first_name} {comment.author.last_name}".strip() or comment.author.email
                    comment_preview = comment.content[:50] if len(comment.content) > 50 else comment.content
                    notify_post_commented(
                        user=comment.post.author,
                        commenter_name=commenter_name,
                        post_id=comment.post.id,
                        comment_preview=comment_preview
                    )
                except Exception:
                    pass  # Don't fail if notification fails

            return success_response(message="Comment approved successfully.", data=CommentModerationSerializer(comment).data)

        elif action == 'reject':
            comment.status = 'rejected'
            comment.reviewed_by = request.user
            comment.reviewed_at = timezone.now()
            comment.rejection_reason = rejection_reason
            comment.save()
            return success_response(message="Comment rejected.", data=CommentModerationSerializer(comment).data)

        return validation_error_response({"action": "Invalid action. Use 'approve' or 'reject'."})


# ==========================================
# CHALLENGES
# ==========================================

class SavingsChallengeListCreateAPIView(APIView):
    """
    List challenges or create a new one.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        challenges = SavingsChallenge.objects.all()

        # Filter by group
        group_id = request.query_params.get('group')
        if group_id:
            challenges = challenges.filter(group_id=group_id)

        # Filter by status
        challenge_status = request.query_params.get('status')
        if challenge_status:
            challenges = challenges.filter(status=challenge_status)

        serializer = SavingsChallengeSerializer(challenges, many=True, context={'request': request})
        return success_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = SavingsChallengeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Check if user is admin/moderator of the group
            group_id = serializer.validated_data.get('group')
            membership = GroupMembership.objects.filter(
                group=group_id,
                user=request.user,
                is_active=True,
                role__in=['admin', 'moderator']
            ).first()

            if not membership:
                return error_response(
                    message="Only group admins/moderators can create challenges.",
                    status_code=status.HTTP_403_FORBIDDEN
                )

            challenge = serializer.save(created_by=request.user)
            return success_response(
                message="Challenge created successfully.",
                data=SavingsChallengeSerializer(challenge, context={'request': request}).data
            )
        return validation_error_response(serializer.errors)


class ChallengeJoinAPIView(APIView):
    """
    Join a savings challenge.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        challenge = get_object_or_404(SavingsChallenge, pk=pk)

        # Check if user is member of the group
        membership = GroupMembership.objects.filter(
            group=challenge.group,
            user=request.user,
            is_active=True
        ).first()

        if not membership:
            return error_response(
                message="You must be a member of the group to join this challenge.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Check if already participating
        existing = ChallengeParticipation.objects.filter(challenge=challenge, user=request.user).first()
        if existing and existing.is_active:
            return error_response(message="You are already participating in this challenge.", status_code=status.HTTP_400_BAD_REQUEST)

        # Create or reactivate participation
        if existing:
            existing.is_active = True
            existing.save()
            participation = existing
        else:
            participation = ChallengeParticipation.objects.create(
                challenge=challenge,
                user=request.user
            )

        # Send notification
        try:
            create_notification(
                user=request.user,
                title=f"Joined Challenge: {challenge.title}",
                message=f"You've joined the {challenge.title} savings challenge. Good luck!",
                notification_type='challenge_joined',
                data={
                    'challenge_title': challenge.title,
                    'challenge_id': str(challenge.id),
                    'goal_amount': str(challenge.goal_amount)
                },
                action_url=f'/community/challenges/{challenge.id}',
                send_push=False  # Don't send push for challenge join
            )
        except Exception:
            pass  # Don't fail if notification fails

        return success_response(
            message="Successfully joined the challenge.",
            data=ChallengeParticipationSerializer(participation).data
        )


class ChallengeUpdateProgressAPIView(APIView):
    """
    Update progress for a challenge participation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        participation = get_object_or_404(ChallengeParticipation, pk=pk, user=request.user, is_active=True)

        amount = request.data.get('current_amount')
        if amount is None:
            return validation_error_response({"current_amount": "This field is required."})

        try:
            amount = float(amount)
            if amount < 0:
                return validation_error_response({"current_amount": "Amount must be positive."})
        except (ValueError, TypeError):
            return validation_error_response({"current_amount": "Invalid amount."})

        # Track if was already completed before
        was_completed = participation.is_completed

        participation.current_amount = amount

        # Check if completed
        if amount >= float(participation.challenge.goal_amount):
            participation.is_completed = True
            participation.completed_at = timezone.now()

        participation.save()

        # Send notification if just completed (not already completed)
        if participation.is_completed and not was_completed:
            try:
                notify_challenge_completed(
                    user=request.user,
                    challenge_name=participation.challenge.title,
                    challenge_id=participation.challenge.id
                )
            except Exception:
                pass  # Don't fail if notification fails

        return success_response(
            message="Progress updated successfully.",
            data=ChallengeParticipationSerializer(participation).data
        )


# ==========================================
# LEADERBOARD
# ==========================================

class GroupLeaderboardAPIView(APIView):
    """
    Get leaderboard for a specific group.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id, *args, **kwargs):
        group = get_object_or_404(CommunityGroup, pk=group_id, is_active=True)

        # Check if user is member
        membership = group.memberships.filter(user=request.user, is_active=True).first()
        if not membership:
            return error_response(
                message="You must be a member of this group to view the leaderboard.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        leaderboard = group.leaderboard_entries.all()

        serializer = GroupLeaderboardSerializer(leaderboard, many=True, context={'request': request})
        return success_response(serializer.data)


class CommunityStatsAPIView(APIView):
    """
    Get overall community statistics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from django.db.models import Sum

        total_members = GroupMembership.objects.filter(is_active=True).values('user').distinct().count()

        # Get total savings from active group members
        all_member_ids = GroupMembership.objects.filter(is_active=True).values_list('user_id', flat=True).distinct()
        from savings.models import SavingsGoalModel
        total_saved = SavingsGoalModel.objects.filter(
            user_id__in=all_member_ids,
            status='active'
        ).aggregate(total=Sum('current_amount'))['total'] or 0

        total_groups = CommunityGroup.objects.filter(is_active=True).count()
        total_posts = CommunityPost.objects.filter(status='approved').count()
        total_challenges = SavingsChallenge.objects.filter(status='active').count()

        stats = {
            'total_members': total_members,
            'total_saved': str(total_saved),
            'total_groups': total_groups,
            'total_posts': total_posts,
            'total_challenges': total_challenges
        }

        return success_response(stats)
