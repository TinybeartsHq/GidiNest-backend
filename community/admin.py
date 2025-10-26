from django.contrib import admin
from .models import CommunityPost, CommunityComment


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author_email', 'likes_count', 'views_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'content', 'author__email')
    readonly_fields = ('likes_count', 'views_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = 'Author Email'


@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ('post_title', 'author_email', 'short_content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__email', 'post__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('created_at',)

    def author_email(self, obj):
        return obj.author.email
    author_email.short_description = 'Author Email'

    def post_title(self, obj):
        return obj.post.title
    post_title.short_description = 'Post Title'

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Comment'
