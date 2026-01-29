from apps.accounts.models import User
from rest_framework.permissions import BasePermission

ROLE_HIERARCHY = {
    User.Role.EDITOR: 1,
    User.Role.ADMIN: 2,
}


class HasMinRole(BasePermission):
    min_role: str | None = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if self.min_role is None:
            return True

        return ROLE_HIERARCHY.get(request.user.role, 0) >= ROLE_HIERARCHY.get(
            self.min_role, 0
        )


class IsEditor(HasMinRole):
    min_role = User.Role.EDITOR


class IsAdmin(HasMinRole):
    min_role = User.Role.ADMIN


class IsOwner(BasePermission):
    OWNER_FIELDS = ("user", "owner", "author", "uploaded_by")

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if user.role == User.Role.ADMIN:
            return True

        if isinstance(obj, User):
            return obj == user

        for field in self.OWNER_FIELDS:
            if getattr(obj, field, None) == user:
                return True

        return False


class CanChangeUserRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, User):
            return False

        if obj == request.user:
            return False

        return True


class CanViewUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user.role == User.Role.ADMIN or request.user == obj


class CanCreateUpload(IsEditor):
    pass


class CanDeleteUpload(IsOwner):
    pass
