from apps.accounts.permissions import IsAdmin, IsOwner
from apps.accounts.serializers import (
    UserCreateSerializer,
    UserDetailSerializer,
    UserListSerializer,
)
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
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
        if self.action in {"create", "destroy"}:
            return [IsAdmin()]

        if self.action in {"partial_update", "me"}:
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
