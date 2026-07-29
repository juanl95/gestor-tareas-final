from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.iniciar_sesion, name="login"),
    path("logout/", views.cerrar_sesion, name="logout"),
    path("", views.pizarra, name="pizarra"),
    path(
        "tareas/<int:tarea_id>/",
        views.detalle_tarea,
        name="detalle_tarea",
    ),
    path(
        "tareas/<int:tarea_id>/completar/",
        views.completar_tarea,
        name="completar_tarea",
    ),
    path(
        "tareas/<int:tarea_id>/editar/",
        views.editar_tarea,
        name="editar_tarea",
    ),
    path(
        "tareas/<int:tarea_id>/eliminar/",
        views.eliminar_tarea,
        name="eliminar_tarea",
    ),
    path(
        "completadas/",
        views.historial_completadas,
        name="historial_completadas",
    ),
    # Compatibilidad con enlaces anteriores del historial.
    path(
        "completadas/<int:tarea_id>/",
        views.detalle_tarea,
        name="detalle_completada",
    ),
]
