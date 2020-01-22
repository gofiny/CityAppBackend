from django.urls import path
from .views import register_user, get_map, get_status, gen_objects, get_profile

urlpatterns = [
    path("", get_status),
    path("register_user", register_user),
    path("get_map", get_map),
    path("gen_objects", gen_objects),
    path("get_profile", get_profile)
]
