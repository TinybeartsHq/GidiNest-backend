# community/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import (
    CommunityGroup, GroupMembership, CommunityPost, CommunityComment,
    PostLike, SavingsChallenge, ChallengeParticipation, GroupLeaderboard
)


class GroupMembershipSerializer(serializers.ModelSerializer):
    """Serializer for group membership with user details."""
    user_id = serializers.ReadOnlyField(source='user.id')
    user_email = serializers.ReadOnlyField(source='user.email')
    user_first_name = serializers.ReadOnlyField(source='user.first_name')
    user_last_name = serializers.ReadOnlyField(source='user.last_name')
    user_savings = serializers.ReadOnlyField()

    class Meta:
        model = GroupMembership
        fields = [
            'id', 'user_id', 'user_email', 'user_first_name', 'user_last_name',
            'role', 'joined_at', 'is_active', 'user_savings'
        ]
        read_only_fields = ['id', 'joined_at', 'user_savings']


class CommunityGroupListSerializer(serializers.ModelSerializer):
    """Serializer for listing community groups."""
    member_count = serializers.ReadOnlyField()
    total_savings = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = CommunityGroup
        fields = [
            'id', 'name', 'description', 'category', 'privacy', 'badge',
            'icon', 'cover_image', 'member_count', 'total_savings',
            'created_by', 'created_by_name', 'created_at', 'is_active',
            'is_member', 'user_role'
        ]
        read_only_fields = ['id', 'created_at', 'member_count', 'total_savings']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return None

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.memberships.filter(user=request.user, is_active=True).exists()
        return False

    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.memberships.filter(user=request.user, is_active=True).first()
            if membership:
                return membership.role
        return None


class CommunityGroupDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single community group."""
    member_count = serializers.ReadOnlyField()
    total_savings = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    members = GroupMembershipSerializer(source='memberships', many=True, read_only=True)
    is_member = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    admins = serializers.SerializerMethodField()

    class Meta:
        model = CommunityGroup
        fields = [
            'id', 'name', 'description', 'category', 'privacy', 'badge',
            'icon', 'cover_image', 'member_count', 'total_savings',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'is_active', 'members', 'is_member', 'user_role', 'admins'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'member_count', 'total_savings']

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return None

    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.memberships.filter(user=request.user, is_active=True).exists()
        return False

    def get_user_role(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            membership = obj.memberships.filter(user=request.user, is_active=True).first()
            if membership:
                return membership.role
        return None

    def get_admins(self, obj):
        admin_memberships = obj.memberships.filter(role__in=['admin', 'moderator'], is_active=True)
        return [{
            'user_id': m.user.id,
            'user_name': f"{m.user.first_name} {m.user.last_name}".strip() or m.user.email,
            'role': m.role
        } for m in admin_memberships]


class CommunityCommentSerializer(serializers.ModelSerializer):
    """Serializer for community comments."""
    author_email = serializers.ReadOnlyField(source='author.email')
    author_id = serializers.ReadOnlyField(source='author.id')
    author_first_name = serializers.ReadOnlyField(source='author.first_name')
    author_last_name = serializers.ReadOnlyField(source='author.last_name')
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = CommunityComment
        fields = [
            'id', 'post', 'author', 'author_id', 'author_email',
            'author_first_name', 'author_last_name', 'author_name',
            'content', 'status', 'reviewed_by', 'reviewed_at',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'author_id', 'author_email', 'author_first_name',
            'author_last_name', 'author_name', 'status', 'reviewed_by',
            'reviewed_at', 'created_at', 'updated_at'
        ]

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.email


class CommunityPostSerializer(serializers.ModelSerializer):
    """Serializer for community posts (list view)."""
    author_email = serializers.ReadOnlyField(source='author.email')
    author_id = serializers.ReadOnlyField(source='author.id')
    author_first_name = serializers.ReadOnlyField(source='author.first_name')
    author_last_name = serializers.ReadOnlyField(source='author.last_name')
    author_name = serializers.SerializerMethodField()
    group_name = serializers.ReadOnlyField(source='group.name')
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'group', 'group_name', 'author', 'author_id', 'author_email',
            'author_first_name', 'author_last_name', 'author_name',
            'title', 'content', 'image_url', 'status', 'likes_count',
            'views_count', 'comments_count', 'created_at', 'updated_at',
            'is_liked'
        ]
        read_only_fields = [
            'id', 'author', 'author_id', 'author_email', 'author_first_name',
            'author_last_name', 'author_name', 'group_name', 'status',
            'likes_count', 'views_count', 'comments_count', 'created_at',
            'updated_at', 'is_liked'
        ]

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.email

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class CommunityPostDetailedSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single post with comments."""
    author_email = serializers.ReadOnlyField(source='author.email')
    author_id = serializers.ReadOnlyField(source='author.id')
    author_first_name = serializers.ReadOnlyField(source='author.first_name')
    author_last_name = serializers.ReadOnlyField(source='author.last_name')
    author_name = serializers.SerializerMethodField()
    group_name = serializers.ReadOnlyField(source='group.name')
    comments = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'group', 'group_name', 'author', 'author_id', 'author_email',
            'author_first_name', 'author_last_name', 'author_name',
            'title', 'content', 'image_url', 'status', 'reviewed_by',
            'reviewed_at', 'rejection_reason', 'likes_count', 'views_count',
            'comments_count', 'created_at', 'updated_at', 'comments', 'is_liked'
        ]
        read_only_fields = [
            'id', 'author', 'author_id', 'author_email', 'author_first_name',
            'author_last_name', 'author_name', 'group_name', 'status',
            'reviewed_by', 'reviewed_at', 'likes_count', 'views_count',
            'comments_count', 'created_at', 'updated_at', 'comments', 'is_liked'
        ]

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.email

    def get_comments(self, obj):
        # Only return approved comments
        approved_comments = obj.comments.filter(status='approved')
        return CommunityCommentSerializer(approved_comments, many=True).data

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class PostLikeSerializer(serializers.ModelSerializer):
    """Serializer for post likes."""
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = PostLike
        fields = ['id', 'post', 'user', 'user_email', 'user_name', 'created_at']
        read_only_fields = ['id', 'user', 'user_email', 'user_name', 'created_at']

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class ChallengeParticipationSerializer(serializers.ModelSerializer):
    """Serializer for challenge participation."""
    user_id = serializers.ReadOnlyField(source='user.id')
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = ChallengeParticipation
        fields = [
            'id', 'challenge', 'user', 'user_id', 'user_email', 'user_name',
            'current_amount', 'is_completed', 'is_active', 'progress_percentage',
            'joined_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_id', 'user_email', 'user_name',
            'progress_percentage', 'joined_at', 'completed_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class SavingsChallengeSerializer(serializers.ModelSerializer):
    """Serializer for savings challenges."""
    group_name = serializers.ReadOnlyField(source='group.name')
    participant_count = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    is_participating = serializers.SerializerMethodField()
    user_participation = serializers.SerializerMethodField()

    class Meta:
        model = SavingsChallenge
        fields = [
            'id', 'group', 'group_name', 'title', 'description', 'icon',
            'goal_amount', 'reward', 'reward_description', 'start_date',
            'end_date', 'status', 'participant_count', 'days_remaining',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'is_participating', 'user_participation'
        ]
        read_only_fields = [
            'id', 'group_name', 'participant_count', 'days_remaining',
            'created_by_name', 'created_at', 'updated_at', 'is_participating',
            'user_participation'
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.email
        return None

    def get_is_participating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.participations.filter(user=request.user, is_active=True).exists()
        return False

    def get_user_participation(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            participation = obj.participations.filter(user=request.user, is_active=True).first()
            if participation:
                return {
                    'current_amount': str(participation.current_amount),
                    'progress_percentage': participation.progress_percentage,
                    'is_completed': participation.is_completed
                }
        return None


class GroupLeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for group leaderboard entries."""
    user_id = serializers.ReadOnlyField(source='user.id')
    user_email = serializers.ReadOnlyField(source='user.email')
    user_name = serializers.SerializerMethodField()
    trend = serializers.ReadOnlyField()

    class Meta:
        model = GroupLeaderboard
        fields = [
            'id', 'group', 'user', 'user_id', 'user_email', 'user_name',
            'rank', 'previous_rank', 'total_savings', 'trend', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_id', 'user_email', 'user_name',
            'trend', 'updated_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


# Moderation Serializers
class PostModerationSerializer(serializers.ModelSerializer):
    """Serializer for moderating posts (admin use)."""
    author_name = serializers.SerializerMethodField()
    group_name = serializers.ReadOnlyField(source='group.name')

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'group', 'group_name', 'author', 'author_name', 'title',
            'content', 'image_url', 'status', 'reviewed_by', 'reviewed_at',
            'rejection_reason', 'created_at'
        ]
        read_only_fields = ['id', 'group', 'author', 'author_name', 'group_name', 'created_at']

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.email


class CommentModerationSerializer(serializers.ModelSerializer):
    """Serializer for moderating comments (admin use)."""
    author_name = serializers.SerializerMethodField()
    post_title = serializers.ReadOnlyField(source='post.title')

    class Meta:
        model = CommunityComment
        fields = [
            'id', 'post', 'post_title', 'author', 'author_name', 'content',
            'status', 'reviewed_by', 'reviewed_at', 'rejection_reason', 'created_at'
        ]
        read_only_fields = ['id', 'post', 'post_title', 'author', 'author_name', 'created_at']

    def get_author_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}".strip() or obj.author.email
