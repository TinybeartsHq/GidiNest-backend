from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    CommunityGroup, GroupMembership, CommunityPost, CommunityComment,
    PostLike, SavingsChallenge, ChallengeParticipation, GroupLeaderboard
)


@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'badge', 'privacy', 'member_count_display', 'total_savings_display', 'is_active', 'created_at')
    list_filter = ('category', 'privacy', 'badge', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'member_count_display', 'total_savings_display')
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'privacy', 'badge')
        }),
        ('Media', {
            'fields': ('icon', 'cover_image')
        }),
        ('Management', {
            'fields': ('created_by', 'is_active')
        }),
        ('Statistics', {
            'fields': ('member_count', 'total_savings_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def member_count_display(self, obj):
        try:
            return obj.member_count
        except Exception:
            return 0
    member_count_display.short_description = 'Members'

    def total_savings_display(self, obj):
        try:
            return f"₦{obj.total_savings:,.2f}"
        except Exception:
            return "₦0.00"
    total_savings_display.short_description = 'Total Savings'


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'group_name', 'role', 'user_savings_display', 'joined_at', 'is_active')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'group__name')
    readonly_fields = ('joined_at', 'user_savings_display')
    ordering = ('-joined_at',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'

    def group_name(self, obj):
        return obj.group.name
    group_name.short_description = 'Group'

    def user_savings_display(self, obj):
        return f"₦{obj.user_savings:,.2f}"
    user_savings_display.short_description = 'User Savings'


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_email', 'group_name', 'status_badge', 'likes_count', 'views_count', 'comments_count', 'created_at')
    list_filter = ('status', 'created_at', 'group')
    search_fields = ('title', 'content', 'author__email', 'group__name')
    readonly_fields = ('likes_count', 'views_count', 'comments_count', 'created_at', 'updated_at', 'reviewed_at')
    ordering = ('-created_at',)
    actions = ['approve_posts', 'reject_posts']

    fieldsets = (
        ('Post Information', {
            'fields': ('group', 'author', 'title', 'content', 'image_url')
        }),
        ('Moderation', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('likes_count', 'views_count', 'comments_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = 'Author'

    def group_name(self, obj):
        return obj.group.name if obj.group else 'No Group'
    group_name.short_description = 'Group'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        return format_html(
            '<span style="padding: 3px 10px; border-radius: 3px; background-color: {}; color: white;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def approve_posts(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} posts were approved.')
    approve_posts.short_description = 'Approve selected posts'

    def reject_posts(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason='Rejected by admin'
        )
        self.message_user(request, f'{updated} posts were rejected.')
    reject_posts.short_description = 'Reject selected posts'


@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ('short_content', 'author_email', 'post_title', 'status_badge', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('content', 'author__email', 'post__title')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')
    ordering = ('created_at',)
    actions = ['approve_comments', 'reject_comments']

    fieldsets = (
        ('Comment Information', {
            'fields': ('post', 'author', 'content')
        }),
        ('Moderation', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = 'Author'

    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Post'

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Comment'

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        return format_html(
            '<span style="padding: 3px 10px; border-radius: 3px; background-color: {}; color: white;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def approve_comments(self, request, queryset):
        for comment in queryset.filter(status='pending'):
            comment.status = 'approved'
            comment.reviewed_by = request.user
            comment.reviewed_at = timezone.now()
            comment.save()
            # Update post comment count
            comment.post.comments_count += 1
            comment.post.save(update_fields=['comments_count'])
        self.message_user(request, f'{queryset.count()} comments were approved.')
    approve_comments.short_description = 'Approve selected comments'

    def reject_comments(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason='Rejected by admin'
        )
        self.message_user(request, f'{updated} comments were rejected.')
    reject_comments.short_description = 'Reject selected comments'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'post_title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'post__title')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Post'


@admin.register(SavingsChallenge)
class SavingsChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'group_name', 'goal_amount', 'status', 'participant_count_display', 'days_remaining_display', 'start_date', 'end_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'group__name')
    readonly_fields = ('created_at', 'updated_at', 'participant_count_display', 'days_remaining_display')
    ordering = ('-created_at',)

    fieldsets = (
        ('Challenge Information', {
            'fields': ('group', 'title', 'description', 'icon')
        }),
        ('Goals & Rewards', {
            'fields': ('goal_amount', 'reward', 'reward_description')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'status')
        }),
        ('Management', {
            'fields': ('created_by', 'created_at', 'updated_at', 'participant_count_display', 'days_remaining_display'),
            'classes': ('collapse',)
        }),
    )

    def group_name(self, obj):
        return obj.group.name if obj.group else 'N/A'
    group_name.short_description = 'Group'

    def participant_count_display(self, obj):
        try:
            return obj.participant_count
        except Exception:
            return 0
    participant_count_display.short_description = 'Participants'

    def days_remaining_display(self, obj):
        try:
            return obj.days_remaining
        except Exception:
            return 0
    days_remaining_display.short_description = 'Days Remaining'


@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'challenge_title', 'current_amount', 'progress_bar', 'is_completed', 'joined_at')
    list_filter = ('is_completed', 'is_active', 'joined_at')
    search_fields = ('user__email', 'challenge__title')
    readonly_fields = ('joined_at', 'completed_at', 'progress_percentage_display')
    ordering = ('-current_amount',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def challenge_title(self, obj):
        return obj.challenge.title
    challenge_title.short_description = 'Challenge'

    def progress_percentage_display(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage_display.short_description = 'Progress'

    def progress_bar(self, obj):
        percentage = min(100, obj.progress_percentage)
        return format_html(
            '<div style="width: 100px; height: 20px; border: 1px solid #ccc; border-radius: 3px;">'
            '<div style="width: {}%; height: 100%; background-color: {}; border-radius: 3px;"></div>'
            '</div>',
            percentage,
            'green' if percentage >= 100 else 'orange'
        )
    progress_bar.short_description = 'Progress'


@admin.register(GroupLeaderboard)
class GroupLeaderboardAdmin(admin.ModelAdmin):
    list_display = ('rank', 'user_email', 'group_name', 'total_savings', 'trend_indicator', 'updated_at')
    list_filter = ('group', 'updated_at')
    search_fields = ('user__email', 'group__name')
    readonly_fields = ('updated_at', 'trend_display')
    ordering = ('group', 'rank')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def group_name(self, obj):
        return obj.group.name
    group_name.short_description = 'Group'

    def trend_indicator(self, obj):
        try:
            trend = obj.trend
        except Exception:
            trend = 'same'
        symbols = {
            'up': '⬆️ Up',
            'down': '⬇️ Down',
            'same': '➡️ Same'
        }
        colors = {
            'up': 'green',
            'down': 'red',
            'same': 'gray'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(trend, 'gray'),
            symbols.get(trend, '➡️ Same')
        )
    trend_indicator.short_description = 'Trend'

    def trend_display(self, obj):
        """Display trend in readonly field"""
        try:
            trend = obj.trend
            symbols = {
                'up': '⬆️ Up',
                'down': '⬇️ Down',
                'same': '➡️ Same'
            }
            return symbols.get(trend, '➡️ Same')
        except Exception:
            return '➡️ Same'
    trend_display.short_description = 'Trend'
