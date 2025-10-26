# community/models.py
from django.db import models
from django.conf import settings # To link to your User model

class CommunityPost(models.Model):
    """
    Represents a single post in the community forum.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts',
        help_text="The user who created this post."
    )
    title = models.CharField(max_length=255, help_text="Title of the community post.")
    content = models.TextField(help_text="Full content of the community post.")
    likes_count = models.PositiveIntegerField(default=0, help_text="Number of likes the post has received.")
    views_count = models.PositiveIntegerField(default=0, help_text="Number of likes the post has received.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the post was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the post was last updated.")

    class Meta:
        verbose_name = "Community Post"
        verbose_name_plural = "Community Posts"
        ordering = ['-created_at'] # Newest posts first

    def __str__(self):
        return f"{self.title} by {self.author.email}"

class CommunityComment(models.Model):
    """
    Represents a comment made on a community post.
    """
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
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the comment was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the comment was last updated.")

    class Meta:
        verbose_name = "Community Comment"
        verbose_name_plural = "Community Comments"
        ordering = ['created_at'] # Oldest comments first

    def __str__(self):
        return f"Comment by {self.author.email} on {self.post.title}"
