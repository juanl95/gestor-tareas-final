from functools import wraps

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import PostIt


User = get_user_model()


def superusuario_requerido(view_function):
    """Impide que usuarios normales entren a acciones administrativas."""

    @wraps(view_function)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_function(request, *args, **kwargs)

    return wrapper


def _usuarios_asignables():
    return User.objects.filter(
        is_active=True,
        is_superuser=False,
    ).order_by("first_name", "last_name", "username")


def _actualizar_tiquets_vencidos():
    """El servidor marca como vencidos los contadores agotados."""
    return PostIt.objects.filter(
        estado=PostIt.ESTADO_EN_PROGRESO,
        vence_el__isnull=False,
        vence_el__lte=timezone.now(),
    ).update(estado=PostIt.ESTADO_VENCIDO)


def _iniciar_siguiente_tiquet(usuario):
    """Mantiene como máximo un tiquet activo por usuario."""
    if usuario.is_superuser:
        return None

    _actualizar_tiquets_vencidos()

    with transaction.atomic():
        activo = (
            PostIt.objects.select_for_update()
            .filter(
                asignado_a=usuario,
                estado=PostIt.ESTADO_EN_PROGRESO,
            )
            .order_by("aceptado_el", "id")
            .first()
        )

        if activo:
            return activo

        siguiente = (
            PostIt.objects.select_for_update()
            .filter(
                asignado_a=usuario,
                estado=PostIt.ESTADO_ASIGNADO,
            )
            .order_by("creado_el", "id")
            .first()
        )

        if siguiente:
            siguiente.iniciar_contador()

        return siguiente


def _tiquets_visibles(usuario):
    queryset = PostIt.objects.select_related("asignado_a", "creado_por")

    if usuario.is_superuser:
        return queryset

    return queryset.filter(asignado_a=usuario)


def _obtener_tiquet_visible(usuario, tarea_id, **filtros):
    return get_object_or_404(
        _tiquets_visibles(usuario),
        pk=tarea_id,
        **filtros,
    )


def _orden_pizarra_usuario(queryset):
    return queryset.annotate(
        prioridad_estado=Case(
            When(estado=PostIt.ESTADO_EN_PROGRESO, then=Value(0)),
            When(estado=PostIt.ESTADO_ASIGNADO, then=Value(1)),
            When(estado=PostIt.ESTADO_VENCIDO, then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by("prioridad_estado", "creado_el", "id")


def _contexto_resumen(usuario):
    queryset = _tiquets_visibles(usuario)

    return {
        "total_tareas": queryset.count(),
        "total_pendientes": queryset.filter(
            estado__in=[
                PostIt.ESTADO_ASIGNADO,
                PostIt.ESTADO_EN_PROGRESO,
            ]
        ).count(),
        "total_en_progreso": queryset.filter(
            estado=PostIt.ESTADO_EN_PROGRESO
        ).count(),
        "total_completadas": queryset.filter(
            estado=PostIt.ESTADO_COMPLETADO
        ).count(),
        "total_vencidas": queryset.filter(
            estado=PostIt.ESTADO_VENCIDO
        ).count(),
    }


def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect("pizarra")

    siguiente = request.POST.get("next") or request.GET.get("next", "")

    if request.method == "POST":
        usuario = request.POST.get("username", "").strip()
        clave = request.POST.get("password", "")

        if not usuario or not clave:
            messages.error(request, "Ingresa tu usuario y contraseña.")
        else:
            user = authenticate(request, username=usuario, password=clave)

            if user is None:
                messages.error(
                    request,
                    "El usuario o la contraseña son incorrectos.",
                )
            else:
                auth_login(request, user)
                messages.success(
                    request,
                    f"Bienvenido, {user.get_short_name() or user.username}.",
                )

                if siguiente and url_has_allowed_host_and_scheme(
                    url=siguiente,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    return redirect(siguiente)

                return redirect("pizarra")

    return render(request, "login.html", {"next": siguiente})


@login_required
@require_POST
def cerrar_sesion(request):
    auth_logout(request)
    messages.success(request, "Tu sesión se cerró correctamente.")
    return redirect("login")


@login_required
def pizarra(request):
    _actualizar_tiquets_vencidos()

    form_titulo = ""
    form_contenido = ""
    form_importancia = PostIt.IMPORTANCIA_MEDIA
    form_asignado_a = ""
    form_duracion = "60"

    if request.method == "POST":
        if not request.user.is_superuser:
            raise PermissionDenied

        form_titulo = request.POST.get("titulo", "").strip()
        form_contenido = request.POST.get("contenido", "").strip()
        form_importancia = request.POST.get(
            "importancia",
            PostIt.IMPORTANCIA_MEDIA,
        )
        form_asignado_a = request.POST.get("asignado_a", "").strip()
        form_duracion = request.POST.get("duracion_minutos", "60").strip()

        formulario_valido = True
        usuario_asignado = None
        duracion_minutos = 0

        if not form_titulo:
            messages.error(request, "El título del tiquet es obligatorio.")
            formulario_valido = False
        elif len(form_titulo) > 100:
            messages.error(
                request,
                "El título no puede superar los 100 caracteres.",
            )
            formulario_valido = False

        if form_importancia not in dict(PostIt.IMPORTANCIA_CHOICES):
            messages.error(request, "Selecciona una importancia válida.")
            formulario_valido = False

        usuario_asignado = _usuarios_asignables().filter(pk=form_asignado_a).first()
        if usuario_asignado is None:
            messages.error(request, "Selecciona un usuario válido.")
            formulario_valido = False

        try:
            duracion_minutos = int(form_duracion)
            if not 1 <= duracion_minutos <= 10080:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(
                request,
                "La duración debe estar entre 1 y 10080 minutos.",
            )
            formulario_valido = False

        if formulario_valido:
            PostIt.objects.create(
                titulo=form_titulo,
                contenido=form_contenido,
                importancia=form_importancia,
                estado=PostIt.ESTADO_ASIGNADO,
                asignado_a=usuario_asignado,
                creado_por=request.user,
                duracion_minutos=duracion_minutos,
            )
            messages.success(
                request,
                f"Tiquet asignado correctamente a {usuario_asignado.username}.",
            )
            return redirect("pizarra")

    if request.user.is_superuser:
        postits_pendientes = (
            _tiquets_visibles(request.user)
            .exclude(estado=PostIt.ESTADO_COMPLETADO)
            .order_by("creado_el", "id")
        )
    else:
        _iniciar_siguiente_tiquet(request.user)
        postits_pendientes = _orden_pizarra_usuario(
            _tiquets_visibles(request.user).exclude(
                estado=PostIt.ESTADO_COMPLETADO
            )
        )

    contexto = {
        "postits": postits_pendientes,
        "importancias": PostIt.IMPORTANCIA_CHOICES,
        "usuarios": _usuarios_asignables() if request.user.is_superuser else [],
        "form_titulo": form_titulo,
        "form_contenido": form_contenido,
        "form_importancia": form_importancia,
        "form_asignado_a": form_asignado_a,
        "form_duracion": form_duracion,
        **_contexto_resumen(request.user),
    }

    return render(request, "pizarra.html", contexto)


@login_required
def detalle_tarea(request, tarea_id):
    _actualizar_tiquets_vencidos()

    if not request.user.is_superuser:
        _iniciar_siguiente_tiquet(request.user)

    tarea = _obtener_tiquet_visible(request.user, tarea_id)
    tarea.refresh_from_db()

    contexto = {
        "tarea": tarea,
        **_contexto_resumen(request.user),
    }
    return render(request, "detalle.html", contexto)


@login_required
@require_POST
def completar_tarea(request, tarea_id):
    _actualizar_tiquets_vencidos()

    if request.user.is_superuser:
        tarea = get_object_or_404(
            PostIt,
            pk=tarea_id,
        )
    else:
        tarea = get_object_or_404(
            PostIt,
            pk=tarea_id,
            asignado_a=request.user,
        )

    if tarea.estado == PostIt.ESTADO_COMPLETADO:
        messages.info(request, "El tiquet ya estaba completado.")
        return redirect("pizarra")

    if not request.user.is_superuser:
        if tarea.estado != PostIt.ESTADO_EN_PROGRESO:
            messages.error(
                request,
                "Solo puedes completar el tiquet que está actualmente en progreso.",
            )
            return redirect("pizarra")

        if tarea.marcar_vencido_si_corresponde():
            messages.error(
                request,
                "El tiempo del tiquet terminó antes de completarlo.",
            )
            _iniciar_siguiente_tiquet(request.user)
            return redirect("pizarra")

    tarea.estado = PostIt.ESTADO_COMPLETADO
    tarea.completado_el = timezone.now()
    tarea.save(update_fields=["estado", "completado_el"])

    messages.success(request, "El tiquet fue completado correctamente.")

    if tarea.asignado_a_id:
        _iniciar_siguiente_tiquet(tarea.asignado_a)

    return redirect("pizarra")


@superusuario_requerido
def editar_tarea(request, tarea_id):
    _actualizar_tiquets_vencidos()
    tarea = get_object_or_404(PostIt, pk=tarea_id)

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        contenido = request.POST.get("contenido", "").strip()
        importancia = request.POST.get("importancia", tarea.importancia)
        asignado_a_id = request.POST.get("asignado_a", "").strip()
        duracion_texto = request.POST.get(
            "duracion_minutos",
            str(tarea.duracion_minutos),
        ).strip()

        formulario_valido = True
        usuario_asignado = _usuarios_asignables().filter(pk=asignado_a_id).first()
        duracion_minutos = 0

        if not titulo:
            messages.error(request, "El título del tiquet es obligatorio.")
            formulario_valido = False
        elif len(titulo) > 100:
            messages.error(
                request,
                "El título no puede superar los 100 caracteres.",
            )
            formulario_valido = False

        if importancia not in dict(PostIt.IMPORTANCIA_CHOICES):
            messages.error(request, "Selecciona una importancia válida.")
            formulario_valido = False

        if usuario_asignado is None:
            messages.error(request, "Selecciona un usuario válido.")
            formulario_valido = False

        try:
            duracion_minutos = int(duracion_texto)
            if not 1 <= duracion_minutos <= 10080:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(
                request,
                "La duración debe estar entre 1 y 10080 minutos.",
            )
            formulario_valido = False

        if formulario_valido:
            tarea.titulo = titulo
            tarea.contenido = contenido
            tarea.importancia = importancia
            tarea.asignado_a = usuario_asignado
            tarea.duracion_minutos = duracion_minutos

            # Cada edición administrativa vuelve a colocar el tiquet en la cola.
            tarea.estado = PostIt.ESTADO_ASIGNADO
            tarea.aceptado_el = None
            tarea.vence_el = None
            tarea.completado_el = None
            tarea.save()

            messages.success(
                request,
                "El tiquet se actualizó y volvió a la cola de asignados.",
            )
            return redirect("pizarra")

        tarea.titulo = titulo
        tarea.contenido = contenido
        tarea.importancia = importancia
        tarea.asignado_a_id = asignado_a_id or tarea.asignado_a_id
        tarea.duracion_minutos = duracion_minutos or tarea.duracion_minutos

    contexto = {
        "tarea": tarea,
        "importancias": PostIt.IMPORTANCIA_CHOICES,
        "usuarios": _usuarios_asignables(),
        **_contexto_resumen(request.user),
    }
    return render(request, "editar.html", contexto)


@superusuario_requerido
@require_POST
def eliminar_tarea(request, tarea_id):
    tarea = get_object_or_404(PostIt, pk=tarea_id)
    titulo = tarea.titulo
    usuario_afectado = tarea.asignado_a
    tarea.delete()

    messages.success(request, f"El tiquet “{titulo}” fue eliminado.")

    if usuario_afectado:
        _iniciar_siguiente_tiquet(usuario_afectado)

    return redirect("pizarra")


@login_required
def historial_completadas(request):
    _actualizar_tiquets_vencidos()

    postits_completados = _tiquets_visibles(request.user).filter(
        estado=PostIt.ESTADO_COMPLETADO
    ).order_by("-completado_el", "-creado_el")

    contexto = {
        "postits": postits_completados,
        **_contexto_resumen(request.user),
    }
    return render(request, "completadas.html", contexto)
