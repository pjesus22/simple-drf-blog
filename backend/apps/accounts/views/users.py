from apps.accounts.permissions import IsAdmin, IsOwner
from apps.accounts.serializers import (
    PasswordUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        user = self.request.user
        if self.action == "create":
            return UserCreateSerializer

        if self.action == "list" or (self.action == "retrieve" and not user.is_staff):
            return UserListSerializer

        return UserDetailSerializer

    def get_permissions(self):
        if self.action in {"create", "destroy", "change_role"}:
            return [IsAdmin()]

        if self.action in {"partial_update", "me", "set_password"}:
            return [IsOwner()]
        return super().get_permissions()

    @action(detail=False, methods=["get", "patch"])
    def me(self, request, *args, **kwargs):
        user = request.user

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def change_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get("role")

        if new_role not in User.Role.values:
            raise ValidationError(
                {"role": f"Invalid role: Must be one of {tuple(User.Role.values)}"}
            )

        if request.user == user and new_role != User.Role.ADMIN:
            if User.objects.filter(role=User.Role.ADMIN).count() <= 1:
                raise ValidationError(
                    {
                        "role": "You cannot demote yourself if you are the last administrator."
                    }
                )

        user.role = new_role
        user.save(update_fields=["role"])
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def set_password(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.validated_data["old_password"]):
            raise ValidationError({"old_password": "Wrong password"})

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"status": "password set"}, status=200)
