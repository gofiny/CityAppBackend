from django.urls import path
from .views import register_user, get_map, get_status, get_spawn


urlpatterns = [
    path("", get_status),
    path("register_user", register_user),
    path("get_map", get_map),
    path("get_spawn", get_spawn)
]
