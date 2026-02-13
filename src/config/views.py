from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


@extend_schema(exclude=True)
class APIRootView(APIView):
    serializer_class = None

    def get_view_name(self):
        return "API Root"

    def get(self, request, format=None):
        return Response(
            {
                "admin": reverse("admin:index", request=request),
                "api_v1": reverse("v1:api-root", request=request, format=format),
                "schema": reverse("schema", request=request, format=format),
                "docs": reverse("swagger-ui", request=request, format=format),
                "redoc": reverse("redoc", request=request, format=format),
                "health": reverse("health", request=request, format=format),
                "token_obtain_pair": reverse(
                    "token_obtain_pair", request=request, format=format
                ),
                "token_refresh": reverse(
                    "token_refresh", request=request, format=format
                ),
                "token_verify": reverse("token_verify", request=request, format=format),
            }
        )
