from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.exceptions import CannotDemoteLastAdmin, InvalidPassword
from apps.accounts.permissions import CanChangeUserRole, CanViewUser, IsAdmin
from apps.accounts.serializers import (
    ChangeRoleSerializer,
    PasswordResetSerializer,
    PasswordUpdateSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from apps.accounts.services import (
    change_own_password,
    change_user_role,
    force_user_password_change,
)

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
            "force_password_change": PasswordResetSerializer,
            "change_role": ChangeRoleSerializer,
        }
        return serializer_map.get(self.action, self.serializer_class)

    def get_permissions(self):
        permission_map = {
            "list": [IsAdmin],
            "retrieve": [CanViewUser],
            "create": [IsAdmin],
            "update": [IsAdmin],
            "partial_update": [IsAdmin],
            "destroy": [IsAdmin],
            "me": [IsAuthenticated],
            "change_password": [IsAuthenticated],
            "force_password_change": [IsAdmin],
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

        try:
            change_user_role(actor=request.user, target_user=user, new_role=new_role)
        except CannotDemoteLastAdmin as exc:
            raise ValidationError({"role": str(exc)}) from exc

        return Response(UserDetailSerializer(user).data)

    @action(detail=False, methods=["post"], url_path="me/change-password")
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        try:
            change_own_password(
                user=user,
                old_password=serializer.validated_data["old_password"],
                new_password=serializer.validated_data["new_password"],
            )
        except InvalidPassword:
            raise ValidationError({"old_password": "Invalid password"}) from None

        return Response(status=204)

    @action(detail=True, methods=["post"])
    def force_password_change(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        force_user_password_change(
            actor=request.user,
            target_user=user,
            new_password=serializer.validated_data["new_password"],
        )

        return Response(status=204)
