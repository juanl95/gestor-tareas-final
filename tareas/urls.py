from django.urls import path
from . import views

urlpatterns = [
    # Pantalla principal (Pizarra de pendientes)
    path('', views.pizarra, name='pizarra'),
    
    # Acción para marcar como completada
    path('completar/<int:tarea_id>/', views.completar_tarea, name='completar_tarea'),
    
    # Acción para editar un post-it pendiente
    path('editar/<int:tarea_id>/', views.editar_tarea, name='editar_tarea'),
    
    # NUEVA RUTA: Acción para eliminar un post-it pendiente (recibe el ID)
    path('eliminar/<int:tarea_id>/', views.eliminar_tarea, name='eliminar_tarea'),
    
    # Pantalla del archivo histórico (Lista simple)
    path('completadas/', views.historial_completadas, name='historial_completadas'),
    
    # Ver detalle de solo lectura de una tarea completada
    path('completada/<int:tarea_id>/', views.detalle_completada, name='detalle_completada'),
]