from rest_framework.routers import DefaultRouter

from .views import DoctorViewSet, ServiceViewSet


router = DefaultRouter()

router.register('doctors', DoctorViewSet, basename='doctor')
router.register('services', ServiceViewSet, basename='service')


urlpatterns = router.urls