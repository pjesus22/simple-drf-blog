from apps.users.models import User
from rest_framework import permissions


class IsEditor(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.role in ["editor", "admin"]


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if isinstance(obj, User):
            return obj == request.user or request.user.role == "admin"

        owner = getattr(obj, "user", None) or getattr(obj, "uploaded_by", None)
        return (owner == request.user) or request.user.role == "admin"


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == "admin"
