# community/serializers.py
from rest_framework import serializers
from .models import CommunityPost, CommunityComment



class CommunityCommentSerializer(serializers.ModelSerializer):
    author_email = serializers.ReadOnlyField(source='author.email')
    author_id = serializers.ReadOnlyField(source='author.id')
    author_first_name = serializers.ReadOnlyField(source='author.first_name')
    author_last_name = serializers.ReadOnlyField(source='author.last_name')
  

    class Meta:
        model = CommunityComment
        fields = ['id', 'author_email','author_last_name','author_first_name', 'author_id', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author_email','author_last_name','author_first_name', 'author_id', 'created_at', 'updated_at'] 

class CommunityPostDetailedSerializer(serializers.ModelSerializer):
    author_email = serializers.ReadOnlyField(source='author.email')
    author_id = serializers.ReadOnlyField(source='author.id')
    author_first_name = serializers.ReadOnlyField(source='author.first_name')
    author_last_name = serializers.ReadOnlyField(source='author.last_name')
    comments = CommunityCommentSerializer(many=True, read_only=True)

    class Meta:
        model = CommunityPost
        fields = [
            'id', 'author', 'author_email','author_last_name','author_first_name', 'author_id', 'title', 'content',
            'likes_count','views_count', 'created_at', 'updated_at', 'comments' # Include comments here
        ]
        read_only_fields = ['id', 'author','author_last_name','author_first_name', 'author_email', 'author_id', 'likes_count','views_count', 'created_at', 'updated_at', 'comments']



class CommunityPostSerializer(serializers.ModelSerializer):
    """
    Serializer for CommunityPost model.
    """
    author_email = serializers.ReadOnlyField(source='author.email')
    author_id = serializers.ReadOnlyField(source='author.id')
    author_first_name = serializers.ReadOnlyField(source='author.first_name')
    author_last_name = serializers.ReadOnlyField(source='author.last_name')

    class Meta:
        model = CommunityPost
        fields = ['id', 'author', 'author_email', 'author_last_name','author_first_name','author_id', 'title', 'content', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'author_email','author_first_name','author_last_name', 'author_id', 'likes_count','views_count', 'created_at', 'updated_at']
