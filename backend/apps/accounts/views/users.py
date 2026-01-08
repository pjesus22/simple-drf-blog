from apps.accounts.models import User
from apps.accounts.permissions import IsAdmin, IsOwner
from apps.accounts.serializers import (
    AdminUserSerializer,
    PrivateUserSerializer,
    PublicUserSerializer,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        user = self.request.user

        if user.is_authenticated and user.role == User.Role.ADMIN:
            return AdminUserSerializer
        if self.action == "me":
            return PrivateUserSerializer

        return PublicUserSerializer

    def get_permissions(self):
        user = self.request.user
        if user.is_authenticated and user.role == User.Role.ADMIN:
            permission_classes = [IsAdmin]
        elif self.action == "me":
            permission_classes = [IsAuthenticated]
        elif self.action == "create":
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsOwner]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get", "patch"])
    def me(self, request, *args, **kwargs):
        user = request.user

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method == "PATCH":
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
