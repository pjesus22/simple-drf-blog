from apps.accounts.permissions import (
    CanChangeUserRole,
    IsAdmin,
)
from apps.accounts.serializers import (
    ChangeRoleSerializer,
    PasswordResetSerializer,
    PasswordUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from django.contrib.auth import get_user_model, update_session_auth_hash
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

User = get_user_model()


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserDetailSerializer

    def get_serializer_class(self):
        serializer_map = {
            "list": UserListSerializer,
            "create": UserCreateSerializer,
            "change_password": PasswordUpdateSerializer,
            "reset_password": PasswordResetSerializer,
            "change_role": ChangeRoleSerializer,
        }
        return serializer_map.get(self.action, self.serializer_class)

    def get_permissions(self):
        permission_map = {
            "list": [IsAdmin],
            "retrieve": [IsAdmin],
            "create": [IsAdmin],
            "me": [IsAuthenticated],
            "change_password": [IsAuthenticated],
            "reset_password": [IsAdmin],
            "change_role": [CanChangeUserRole],
        }
        permission_classes = permission_map.get(self.action, self.permission_classes)
        return [p() for p in permission_classes]

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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_role = serializer.validated_data["role"]

        if request.user == user and new_role != User.Role.ADMIN:
            if User.objects.filter(role=User.Role.ADMIN).count() <= 1:
                raise ValidationError(
                    {
                        "role": "You cannot demote yourself if you are the last administrator."
                    }
                )

        user.role = new_role
        user.save(update_fields=["role"])

        return Response(UserDetailSerializer(user).data)

    @action(detail=False, methods=["post"], url_path="me/change-password")
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            raise ValidationError({"old_password": "Invalid password"})

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        update_session_auth_hash(request, user)

        return Response(status=204)

    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(status=204)
