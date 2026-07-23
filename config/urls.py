from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("tareas.urls")),
]


handler403 = "tareas.error_views.error_403"
handler404 = "tareas.error_views.error_404"
handler500 = "tareas.error_views.error_500"