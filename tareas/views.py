from django.shortcuts import render, redirect, get_object_or_404
from .models import PostIt

# 1. CONTROL DE LA PIZZARRA PRINCIPAL (TAREAS PENDIENTES)
def pizarra(request):
    if request.method == 'POST':
        v_titulo = request.POST.get('titulo')
        v_contenido = request.POST.get('contenido')
        v_color = request.POST.get('color')
        
        PostIt.objects.create(titulo=v_titulo, contenido=v_contenido, color=v_color)
        return redirect('pizarra')

    postits_pendientes = PostIt.objects.filter(completada=False).order_by('-creado_el')
    return render(request, 'pizarra.html', {'postits': postits_pendientes})


# 2. ACCIÓN PARA PASAR LA TAREA A COMPLETADA
def completar_tarea(request, tarea_id):
    tarea = get_object_or_404(PostIt, id=tarea_id)
    tarea.completada = True
    tarea.save()
    return redirect('pizarra')


# 3. ACCIÓN PARA EDITAR UN POST-IT PENDIENTE
def editar_tarea(request, tarea_id):
    tarea = get_object_or_404(PostIt, id=tarea_id)
    
    if tarea.completada:
        return redirect('pizarra')
        
    if request.method == 'POST':
        tarea.titulo = request.POST.get('titulo')
        tarea.contenido = request.POST.get('contenido')
        tarea.color = request.POST.get('color')
        tarea.save()
        return redirect('pizarra')
        
    return render(request, 'editar.html', {'tarea': tarea})


# 4. NUEVA VISTA: ACCIÓN PARA ELIMINAR UNA TAREA PENDIENTE
def eliminar_tarea(request, tarea_id):
    # Buscamos la nota por su ID único
    tarea = get_object_or_404(PostIt, id=tarea_id)
    
    # Seguridad: Solo permitimos borrar si la tarea NO está completada
    if not tarea.completada:
        tarea.delete() # Borra el registro de la base de datos
        
    return redirect('pizarra')


# 5. PANTALLA DEL HISTORIAL (LISTA SIMPLE DE COMPLETADAS)
def historial_completadas(request):
    postits_completados = PostIt.objects.filter(completada=True).order_by('-creado_el')
    return render(request, 'completadas.html', {'postits': postits_completados})


# 6. PANTALLA DE SOLO CONSULTA (DETALLE CERRADO)
def detalle_completada(request, tarea_id):
    tarea = get_object_or_404(PostIt, id=tarea_id)
    return render(request, 'detalle.html', {'tarea': tarea})