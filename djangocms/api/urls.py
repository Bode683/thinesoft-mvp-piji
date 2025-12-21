# todo/todo_api/urls.py : API urls.py
# from django.conf.urls import url
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TodoListApiView,
    TodoDetailApiView,
    TenantViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', TodoListApiView.as_view()),
    path('<int:todo_id>/', TodoDetailApiView.as_view()),
    path('', include(router.urls)),
]


