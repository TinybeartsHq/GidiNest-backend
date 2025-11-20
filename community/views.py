# community/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
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

    @extend_schema(
        tags=['V1 - Community'],
        summary='List Community Posts',
        description='Retrieve a list of all community posts.',
        responses={
            200: {
                'description': 'Posts retrieved successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'data': []
                        }
                    }
                }
            },
            401: {'description': 'Unauthorized'},
        }
    )
    def get(self, request, *args, **kwargs):
        posts = CommunityPost.objects.all()
        serializer = CommunityPostSerializer(posts, many=True)
        return success_response(serializer.data)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Create Community Post',
        description='Create a new community post.',
        request=CommunityPostSerializer,
        responses={
            200: {
                'description': 'Post created successfully',
                'content': {
                    'application/json': {
                        'example': {
                            'success': True,
                            'message': 'Community post created successfully.',
                            'data': {}
                        }
                    }
                }
            },
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
        }
    )
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

    @extend_schema(
        tags=['V1 - Community'],
        summary='Get Community Post',
        description='Retrieve a single community post by ID.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Post ID'),
        ],
        responses={
            200: {'description': 'Post retrieved successfully'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Post not found'},
        }
    )
    def get(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        post.views_count = post.views_count+1
        post.save()
        serializer = CommunityPostDetailedSerializer(post)
        return success_response(serializer.data)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Update Community Post',
        description='Update an existing community post (full update). Only the author can update.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Post ID'),
        ],
        request=CommunityPostDetailedSerializer,
        responses={
            200: {'description': 'Post updated successfully'},
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            403: {'description': 'Forbidden - not the author'},
            404: {'description': 'Post not found'},
        }
    )
    def put(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        serializer = CommunityPostDetailedSerializer(post, data=request.data, partial=False) # partial=False for PUT
        if serializer.is_valid():
            serializer.save()
            return success_response(message= "Community post updated successfully.", data=serializer.data)
        return validation_error_response(serializer.errors)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Partially Update Community Post',
        description='Partially update an existing community post. Only the author can update.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Post ID'),
        ],
        request=CommunityPostDetailedSerializer,
        responses={
            200: {'description': 'Post updated successfully'},
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            403: {'description': 'Forbidden - not the author'},
            404: {'description': 'Post not found'},
        }
    )
    def patch(self, request, pk, *args, **kwargs):
        post = self.get_object(pk)
        serializer = CommunityPostDetailedSerializer(post, data=request.data, partial=True) # partial=True for PATCH
        if serializer.is_valid():
            serializer.save()
            return success_response(message= "Community post updated successfully.", data=serializer.data)
           
        return validation_error_response(serializer.errors)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Delete Community Post',
        description='Delete a community post. Only the author can delete.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Post ID'),
        ],
        responses={
            200: {'description': 'Post deleted successfully'},
            401: {'description': 'Unauthorized'},
            403: {'description': 'Forbidden - not the author'},
            404: {'description': 'Post not found'},
        }
    )
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

    @extend_schema(
        tags=['V1 - Community'],
        summary='List Post Comments',
        description='Retrieve all comments for a specific community post.',
        parameters=[
            OpenApiParameter(name='post_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Post ID'),
        ],
        responses={
            200: {'description': 'Comments retrieved successfully'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Post not found'},
        }
    )
    def get(self, request, post_id, *args, **kwargs):
        # Ensure the post exists and is accessible
        post = get_object_or_404(CommunityPost, pk=post_id)
        comments = post.comments.all() # Access comments via related_name
        serializer = CommunityCommentSerializer(comments, many=True)
        return success_response(serializer.data)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Create Comment',
        description='Create a new comment on a specific community post.',
        parameters=[
            OpenApiParameter(name='post_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Post ID'),
        ],
        request=CommunityCommentSerializer,
        responses={
            200: {'description': 'Comment created successfully'},
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Post not found'},
        }
    )
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

    @extend_schema(
        tags=['V1 - Community'],
        summary='Get Comment',
        description='Retrieve a single community comment by ID.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Comment ID'),
        ],
        responses={
            200: {'description': 'Comment retrieved successfully'},
            401: {'description': 'Unauthorized'},
            404: {'description': 'Comment not found'},
        }
    )
    def get(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment)
        return success_response(serializer.data)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Update Comment',
        description='Update an existing comment (full update). Only the author can update.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Comment ID'),
        ],
        request=CommunityCommentSerializer,
        responses={
            200: {'description': 'Comment updated successfully'},
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            403: {'description': 'Forbidden - not the author'},
            404: {'description': 'Comment not found'},
        }
    )
    def put(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return success_response(message="Comment updated successfully.",data= serializer.data)
        return validation_error_response(serializer.errors)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Partially Update Comment',
        description='Partially update an existing comment. Only the author can update.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Comment ID'),
        ],
        request=CommunityCommentSerializer,
        responses={
            200: {'description': 'Comment updated successfully'},
            400: {'description': 'Validation error'},
            401: {'description': 'Unauthorized'},
            403: {'description': 'Forbidden - not the author'},
            404: {'description': 'Comment not found'},
        }
    )
    def patch(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        serializer = CommunityCommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(message="Comment updated successfully.",data= serializer.data)
        return validation_error_response(serializer.errors)

    @extend_schema(
        tags=['V1 - Community'],
        summary='Delete Comment',
        description='Delete a comment. Only the author can delete.',
        parameters=[
            OpenApiParameter(name='pk', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH, description='Comment ID'),
        ],
        responses={
            200: {'description': 'Comment deleted successfully'},
            401: {'description': 'Unauthorized'},
            403: {'description': 'Forbidden - not the author'},
            404: {'description': 'Comment not found'},
        }
    )
    def delete(self, request, pk, *args, **kwargs):
        comment = self.get_object(pk)
        comment.delete()
        return success_response(message="Comment deleted successfully.")