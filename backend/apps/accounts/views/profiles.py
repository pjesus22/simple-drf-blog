from apps.accounts.models import Profile
from apps.accounts.permissions import IsOwner
from apps.accounts.serializers import PrivateProfileSerializer, PublicProfileSerializer
from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


class ProfileViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user

        if self.action in ("update", "partial_update"):
            return Profile.objects.editable_by(user)

        if self.action == "me":
            return Profile.objects.me(user)

        return Profile.objects.visible_for(user)

    def get_serializer_class(self):
        if self.action in ("update", "partial_update", "me"):
            return PrivateProfileSerializer
        return PublicProfileSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update"):
            permission_classes = [IsOwner]
        elif self.action == "me":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [p() for p in permission_classes]

    @action(detail=False, methods=["get", "put", "patch"])
    def me(self, request):
        queryset = Profile.objects.me(request.user)
        profile = get_object_or_404(queryset)

        serializer = self.get_serializer(
            profile,
            data=request.data if request.method != "GET" else None,
            partial=request.method == "PATCH",
        )

        if request.method != "GET":
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(serializer.data)
