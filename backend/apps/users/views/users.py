from apps.users.models import User
from apps.users.permissions import IsAdmin
from apps.users.serializers import (
    AdminUserSerializer,
    PrivateUserSerializer,
    PublicUserSerializer,
)
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        user = self.request.user

        if user.is_authenticated and user.role == "admin":
            return AdminUserSerializer
        if self.action == "me":
            return PrivateUserSerializer

        return PublicUserSerializer

    def get_permissions(self):
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            permission_classes = [IsAdmin]
        elif self.action == "me":
            permission_classes = [IsAuthenticated]
        elif self.action in ("list", "retrieve"):
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        user = request.user

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        elif request.method == "PATCH":
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
