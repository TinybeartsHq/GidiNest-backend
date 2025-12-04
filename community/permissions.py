# community/permissions.py
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of an object to edit or delete it.
    Read permissions are allowed to any authenticated user.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class IsGroupMemberOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only group members to interact with group content.
    Read permissions allowed for public groups.
    """
    def has_object_permission(self, request, view, obj):
        # For models with a group attribute
        group = getattr(obj, 'group', obj if hasattr(obj, 'memberships') else None)

        if not group:
            return False

        # Allow read access for public groups
        if request.method in permissions.SAFE_METHODS and group.privacy == 'public':
            return True

        # Check if user is a member
        if request.user.is_authenticated:
            return group.memberships.filter(user=request.user, is_active=True).exists()

        return False


class IsGroupAdminOrModerator(permissions.BasePermission):
    """
    Permission to check if user is an admin or moderator of the group.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # For models with a group attribute
        group = getattr(obj, 'group', obj if hasattr(obj, 'memberships') else None)

        if not group:
            return False

        membership = group.memberships.filter(user=request.user, is_active=True).first()
        if membership:
            return membership.role in ['admin', 'moderator']

        return False


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Permission to check if user is staff for write operations.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class CanModerateContent(permissions.BasePermission):
    """
    Permission to check if user can moderate content (approve/reject posts/comments).
    Must be staff, superuser, or group admin/moderator.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Staff and superusers can moderate anything
        if request.user.is_staff or request.user.is_superuser:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Staff and superusers can moderate anything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Check if user is admin/moderator of the group
        group = getattr(obj, 'group', None)
        if group:
            membership = group.memberships.filter(user=request.user, is_active=True).first()
            if membership:
                return membership.role in ['admin', 'moderator']

        return False
