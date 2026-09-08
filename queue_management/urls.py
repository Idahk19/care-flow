from rest_framework.routers import DefaultRouter

from .views import QueueEntryViewSet


router = DefaultRouter()

router.register(
    'queue',
    QueueEntryViewSet,
    basename='queue'
)


urlpatterns = router.urls