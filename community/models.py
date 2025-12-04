# community/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum


class CommunityGroup(models.Model):
    """
    Represents a community group where users can join and interact.
    Examples: Expecting Moms Lagos, New Parents 2025, etc.
    """
    CATEGORY_CHOICES = [
        ('pregnancy', 'Pregnancy & Expecting'),
        ('new_parents', 'New Parents'),
        ('general_savings', 'General Savings'),
        ('childbirth', 'Childbirth'),
        ('parenting', 'Parenting'),
        ('other', 'Other'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    BADGE_CHOICES = [
        ('active', 'Active'),
        ('popular', 'Popular'),
        ('featured', 'Featured'),
        ('new', 'New'),
        ('none', 'None'),
    ]

    name = models.CharField(max_length=255, help_text="Name of the community group.")
    description = models.TextField(help_text="Description of the community group.")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, default='none')
    icon = models.URLField(blank=True, null=True, help_text="URL to group icon/image.")
    cover_image = models.URLField(blank=True, null=True, help_text="URL to group cover image.")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        help_text="User who created this group."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True, help_text="Whether the group is active.")

    class Meta:
        verbose_name = "Community Group"
        verbose_name_plural = "Community Groups"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        """Returns the total number of members in the group."""
        return self.memberships.filter(is_active=True).count()

    @property
    def total_savings(self):
        """Returns the total savings of all members in the group."""
        from savings.models import SavingsGoalModel
        member_ids = self.memberships.filter(is_active=True).values_list('user_id', flat=True)
        total = SavingsGoalModel.objects.filter(
            user_id__in=member_ids,
            status='active'
        ).aggregate(total=Sum('current_amount'))['total']
        return total or 0


class GroupMembership(models.Model):
    """
    Represents a user's membership in a community group.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    ]

    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text="The group this membership belongs to."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        help_text="The user who is a member."
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Whether the membership is active.")

    class Meta:
        verbose_name = "Group Membership"
        verbose_name_plural = "Group Memberships"
        unique_together = ['group', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} in {self.group.name} ({self.role})"

    @property
    def user_savings(self):
        """Returns the user's total savings."""
        from savings.models import SavingsGoalModel
        total = SavingsGoalModel.objects.filter(
            user=self.user,
            status='active'
        ).aggregate(total=Sum('current_amount'))['total']
        return total or 0


class CommunityPost(models.Model):
    """
    Represents a single post in a community group.
    Now includes moderation workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name='posts',
        help_text="The group this post belongs to.",
        null=True,
        blank=True
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts',
        help_text="The user who created this post."
    )
    title = models.CharField(max_length=255, help_text="Title of the community post.")
    content = models.TextField(help_text="Full content of the community post.")
    image_url = models.URLField(blank=True, null=True, help_text="URL to attached image.")

    # Moderation fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_posts',
        help_text="Admin/moderator who reviewed this post."
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection.")

    likes_count = models.PositiveIntegerField(default=0, help_text="Number of likes the post has received.")
    views_count = models.PositiveIntegerField(default=0, help_text="Number of views the post has received.")
    comments_count = models.PositiveIntegerField(default=0, help_text="Number of comments on the post.")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the post was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the post was last updated.")

    class Meta:
        verbose_name = "Community Post"
        verbose_name_plural = "Community Posts"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['group', 'status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.author.email} [{self.status}]"


class CommunityComment(models.Model):
    """
    Represents a comment made on a community post.
    Now includes moderation workflow.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="The post this comment belongs to."
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_comments',
        help_text="The user who created this comment."
    )
    content = models.TextField(help_text="Content of the comment.")

    # Moderation fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_comments',
        help_text="Admin/moderator who reviewed this comment."
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection.")

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the comment was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the comment was last updated.")

    class Meta:
        verbose_name = "Community Comment"
        verbose_name_plural = "Community Comments"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'status', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.email} on {self.post.title} [{self.status}]"


class PostLike(models.Model):
    """
    Tracks which users liked which posts.
    """
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name='likes',
        help_text="The post that was liked."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes',
        help_text="The user who liked the post."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Post Like"
        verbose_name_plural = "Post Likes"
        unique_together = ['post', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'user']),
        ]

    def __str__(self):
        return f"{self.user.email} likes {self.post.title}"


class SavingsChallenge(models.Model):
    """
    Represents a savings challenge within a community group.
    """
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name='challenges',
        help_text="The group this challenge belongs to."
    )
    title = models.CharField(max_length=255, help_text="Title of the challenge.")
    description = models.TextField(help_text="Description of the challenge.")
    icon = models.URLField(blank=True, null=True, help_text="URL to challenge icon.")

    goal_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Target savings amount for the challenge."
    )
    reward = models.CharField(max_length=255, blank=True, help_text="Reward for completing the challenge.")
    reward_description = models.TextField(blank=True, help_text="Detailed description of the reward.")

    start_date = models.DateTimeField(help_text="When the challenge starts.")
    end_date = models.DateTimeField(help_text="When the challenge ends.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_challenges',
        help_text="User who created this challenge."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Savings Challenge"
        verbose_name_plural = "Savings Challenges"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', 'status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} in {self.group.name}"

    @property
    def participant_count(self):
        """Returns the number of participants in the challenge."""
        return self.participations.filter(is_active=True).count()

    @property
    def days_remaining(self):
        """Returns the number of days remaining in the challenge."""
        from django.utils import timezone
        if self.status == 'completed' or self.status == 'cancelled':
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)


class ChallengeParticipation(models.Model):
    """
    Tracks user participation in savings challenges.
    """
    challenge = models.ForeignKey(
        SavingsChallenge,
        on_delete=models.CASCADE,
        related_name='participations',
        help_text="The challenge being participated in."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='challenge_participations',
        help_text="The user participating in the challenge."
    )

    current_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current amount saved for this challenge."
    )
    is_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    joined_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Challenge Participation"
        verbose_name_plural = "Challenge Participations"
        unique_together = ['challenge', 'user']
        ordering = ['-current_amount']
        indexes = [
            models.Index(fields=['challenge', '-current_amount']),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.challenge.title}"

    @property
    def progress_percentage(self):
        """Returns the completion percentage."""
        if self.challenge.goal_amount > 0:
            return min(100, (float(self.current_amount) / float(self.challenge.goal_amount)) * 100)
        return 0


class GroupLeaderboard(models.Model):
    """
    Cached leaderboard entries for a community group.
    Updated periodically or on relevant events.
    """
    group = models.ForeignKey(
        CommunityGroup,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        help_text="The group this leaderboard entry belongs to."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        help_text="The user on the leaderboard."
    )

    rank = models.PositiveIntegerField(help_text="Current rank in the group.")
    previous_rank = models.PositiveIntegerField(null=True, blank=True, help_text="Previous rank for trending.")
    total_savings = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Total savings amount."
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Group Leaderboard"
        verbose_name_plural = "Group Leaderboards"
        unique_together = ['group', 'user']
        ordering = ['rank']
        indexes = [
            models.Index(fields=['group', 'rank']),
        ]

    def __str__(self):
        return f"#{self.rank} {self.user.email} in {self.group.name}"

    @property
    def trend(self):
        """Returns 'up', 'down', or 'same' based on rank change."""
        if self.previous_rank is None:
            return 'same'
        if self.rank < self.previous_rank:
            return 'up'
        elif self.rank > self.previous_rank:
            return 'down'
        return 'same'
