from apps.accounts.models import User
from rest_framework import permissions


class IsEditor(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in [User.Role.EDITOR, User.Role.ADMIN]


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if isinstance(obj, User):
            return obj == request.user or request.user.role == User.Role.ADMIN

        owner = getattr(obj, "user", None) or getattr(obj, "uploaded_by", None)
        return (owner == request.user) or request.user.role == User.Role.ADMIN


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == User.Role.ADMIN
