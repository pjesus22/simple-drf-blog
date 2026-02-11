from rest_framework.routers import DefaultRouter

from apps.accounts.views import ProfileViewSet, UserViewSet
from apps.content.views import CategoryViewSet, PostViewSet, TagViewSet
from apps.uploads.views import UploadViewSet


class MasterRouter(DefaultRouter):
    def get_api_root_view(self, api_urls=None):
        root_view = super().get_api_root_view(api_urls=api_urls)
        root_view.cls.__doc__ = "Welcome to the API Browser."
        root_view.cls.get_view_name = lambda self: "API Browser"
        return root_view


router = MasterRouter()

router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"posts", PostViewSet, basename="post")
router.register(r"uploads", UploadViewSet, basename="upload")
router.register(r"users", UserViewSet, basename="user")
router.register(r"profiles", ProfileViewSet, basename="profile")
# router.register(r'<resource_name>', <viewset>, basename='<instance_resource_name>')
