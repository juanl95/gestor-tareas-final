from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Enlazamos las URLs de nuestra aplicación de tareas
    path('', include('tareas.urls')),
]