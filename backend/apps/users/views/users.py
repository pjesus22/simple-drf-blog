from apps.users.models import User
from apps.users.permissions import IsAdmin, IsOwner
from apps.users.serializers import PrivateUserSerializer, PublicUserSerializer
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "me":
            return PrivateUserSerializer
        return PublicUserSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            permission_classes = [AllowAny]
        elif self.action in ("me"):
            permission_classes = [IsAuthenticated]
        elif self.action in ("update", "partial_update", "destroy"):
            permission_classes = [IsOwner]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    @action(
        detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user

        if request.method == "GET":
            serializer = PrivateUserSerializer(user)
            return Response(serializer.data)

        elif request.method == "PATCH":
            serializer = PrivateUserSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
