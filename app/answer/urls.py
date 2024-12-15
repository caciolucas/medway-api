from answer.views import ExamViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r"exams", ExamViewSet, basename="exam")


urlpatterns = [
    path("", include(router.urls)),
]
