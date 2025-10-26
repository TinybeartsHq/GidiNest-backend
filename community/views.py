# community/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from core.helpers.response import success_response, validation_error_response, error_response
from .models import CommunityPost, CommunityComment
from .serializers import CommunityPostDetailedSerializer, CommunityPostSerializer, CommunityCommentSerializer
from .permissions import IsAuthorOrReadOnly


 
class CommunityPostListCreateAPIView(APIView):
    """
    API endpoint for listing all community posts and creating new ones.
    - GET: Retrieve a list of all community posts.
    - POST: Create a new community post.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        posts = CommunityPost.objects.all()
        serializer = CommunityPostSerializer(posts, many=True)
        return success_response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CommunityPostSerializer(data=request.data)
        if serializer.is_valid():
            # Set the author to the currently authenticated user
            serializer.save(author=request.user)
            return success_response(message= "Community post created successfully.", data=serializer.data)
        return validation_error_response(serializer.errors)


class CommunityPostDetailAPIView(APIView):
    """
    API endpoint for retrieving, updating, or deleting a specific community post.
    - GET: Retrieve a single community post.
    - PUT/PATCH: Update an existing community post (only by author).
    - DELETE: Delete an existing community post (only by author).
    """
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_object(self, pk):
        # Helper to get the post or raise 404
        obj = get_object_or_404(CommunityPost, pk=pk)
        # Check object permissions
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        post.views_count = post.views_count+1
        post.save()
        serializer = CommunityPostDetailedSerializer(post)
        return success_response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        serializer = CommunityPostDetailedSerializer(post, data=request.data, partial=False) # partial=False for PUT
        if serializer.is_valid():
            serializer.save()
            return success_response(message= "Community post updated successfully.", data=serializer.data)
        return validation_error_response(serializer.errors)

    def patch(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        serializer = CommunityPostDetailedSerializer(post, data=request.data, partial=True) # partial=True for PATCH
        if serializer.is_valid():
            serializer.save()
            return success_response(message= "Community post updated successfully.", data=serializer.data)
           
        return validation_error_response(serializer.errors)

    def delete(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        post.delete()
        return success_response(message= "Community post deleted successfully")
    
 
class CommunityCommentListCreateAPIView(APIView):
    """
    API endpoint for listing comments for a specific post and creating new comments.
    - GET: Retrieve a list of comments for a given post.
    - POST: Create a new comment on a specific post.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id, *args, **kwargs):
        # Ensure the post exists and is accessible
        post = get_object_or_404(CommunityPost, pk=post_id)
        comments = post.comments.all() # Access comments via related_name
        serializer = CommunityCommentSerializer(comments, many=True)
        return success_response(serializer.data)

    def post(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(CommunityPost, pk=post_id)
        serializer = CommunityCommentSerializer(data=request.data)
        if serializer.is_valid():
            # Set the author to the currently authenticated user and link to the post
            serializer.save(author=request.user, post=post)
            return success_response(message="Comment created successfully.", data= serializer.data)
        return validation_error_response(serializer.errors)


class CommunityCommentDetailAPIView(APIView):
    """
    API endpoint for retrieving, updating, or deleting a specific community comment.
    - GET: Retrieve a single community comment.
    - PUT/PATCH: Update an existing community comment (only by author).
    - DELETE: Delete an existing community comment (only by author).
    """
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_object(self, pk):
        obj = get_object_or_404(CommunityComment, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment)
        return success_response(serializer.data)

    def put(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return success_response(message="Comment updated successfully.",data= serializer.data)
        return validation_error_response(serializer.errors)

    def patch(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(message="Comment updated successfully.",data= serializer.data)
        return validation_error_response(serializer.errors)

    def delete(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        comment.delete()
        return success_response(message="Comment deleted successfully.")