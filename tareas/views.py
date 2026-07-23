from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login as auth_login,
    logout as auth_logout,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import PostIt


User = get_user_model()


def _tareas_permitidas(user):
    queryset = PostIt.objects.select_related("propietario")

    if user.is_staff:
        return queryset

    return queryset.filter(propietario=user)


def _obtener_tarea_permitida(user, tarea_id, **filtros):
    return get_object_or_404(
        _tareas_permitidas(user),
        pk=tarea_id,
        **filtros,
    )


def _contexto_resumen(user):
    queryset = _tareas_permitidas(user)

    return {
        "total_tareas": queryset.count(),
        "total_pendientes": queryset.filter(completada=False).count(),
        "total_completadas": queryset.filter(completada=True).count(),
    }


def _usuarios_asignables():
    return User.objects.filter(is_active=True).order_by("username")


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

    return render(
        request,
        "login.html",
        {
            "next": siguiente,
        },
    )


@login_required
@require_POST
def cerrar_sesion(request):
    auth_logout(request)
    messages.success(request, "Tu sesión se cerró correctamente.")
    return redirect("login")


@login_required
def pizarra(request):
    form_titulo = ""
    form_contenido = ""
    form_color = "#2563eb"
    propietario_seleccionado = str(request.user.pk)

    if request.method == "POST":
        form_titulo = request.POST.get("titulo", "").strip()
        form_contenido = request.POST.get("contenido", "").strip()
        form_color = request.POST.get("color", "#2563eb")

        propietario_seleccionado = request.POST.get(
            "propietario",
            str(request.user.pk),
        ).strip()

        colores_validos = dict(PostIt.COLORES_CHOICES)
        formulario_valido = True
        propietario = request.user

        if not form_titulo:
            messages.error(
                request,
                "El título del tiquet es obligatorio.",
            )
            formulario_valido = False

        elif len(form_titulo) > 100:
            messages.error(
                request,
                "El título no puede superar los 100 caracteres.",
            )
            formulario_valido = False

        if form_color not in colores_validos:
            form_color = "#2563eb"

        if request.user.is_staff:
            propietario = User.objects.filter(
                pk=propietario_seleccionado,
                is_active=True,
            ).first()

            if propietario is None:
                messages.error(
                    request,
                    "Selecciona un propietario válido.",
                )
                formulario_valido = False

        if formulario_valido:
            PostIt.objects.create(
                titulo=form_titulo,
                contenido=form_contenido,
                color=form_color,
                propietario=propietario,
            )

            messages.success(
                request,
                "El tiquet se creó correctamente.",
            )

            return redirect("pizarra")

    postits_pendientes = _tareas_permitidas(
        request.user
    ).filter(completada=False)

    contexto = {
        "postits": postits_pendientes,
        "colores": PostIt.COLORES_CHOICES,
        "usuarios": (
            _usuarios_asignables()
            if request.user.is_staff
            else []
        ),
        "form_titulo": form_titulo,
        "form_contenido": form_contenido,
        "form_color": form_color,
        "propietario_seleccionado": propietario_seleccionado,
        **_contexto_resumen(request.user),
    }

    return render(request, "pizarra.html", contexto)


@login_required
@require_POST
def completar_tarea(request, tarea_id):
    tarea = _obtener_tarea_permitida(
        request.user,
        tarea_id,
        completada=False,
    )

    tarea.completada = True
    tarea.save(update_fields=["completada"])

    messages.success(
        request,
        "El tiquet fue marcado como completado.",
    )

    return redirect("pizarra")


@login_required
def editar_tarea(request, tarea_id):
    tarea = _obtener_tarea_permitida(
        request.user,
        tarea_id,
        completada=False,
    )

    propietario_seleccionado = str(
        tarea.propietario_id or ""
    )

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        contenido = request.POST.get("contenido", "").strip()
        color = request.POST.get("color", tarea.color)

        propietario_seleccionado = request.POST.get(
            "propietario",
            propietario_seleccionado,
        ).strip()

        colores_validos = dict(PostIt.COLORES_CHOICES)
        formulario_valido = True
        nuevo_propietario = tarea.propietario

        if not titulo:
            messages.error(
                request,
                "El título del tiquet es obligatorio.",
            )
            formulario_valido = False

        elif len(titulo) > 100:
            messages.error(
                request,
                "El título no puede superar los 100 caracteres.",
            )
            formulario_valido = False

        if color not in colores_validos:
            color = "#2563eb"

        if request.user.is_staff:
            nuevo_propietario = User.objects.filter(
                pk=propietario_seleccionado,
                is_active=True,
            ).first()

            if nuevo_propietario is None:
                messages.error(
                    request,
                    "Selecciona un propietario válido.",
                )
                formulario_valido = False

        if formulario_valido:
            tarea.titulo = titulo
            tarea.contenido = contenido
            tarea.color = color

            campos_actualizados = [
                "titulo",
                "contenido",
                "color",
            ]

            if request.user.is_staff:
                tarea.propietario = nuevo_propietario
                campos_actualizados.append("propietario")

            tarea.save(update_fields=campos_actualizados)

            messages.success(
                request,
                "El tiquet se actualizó correctamente.",
            )

            return redirect("pizarra")

        tarea.titulo = titulo
        tarea.contenido = contenido
        tarea.color = color

    contexto = {
        "tarea": tarea,
        "colores": PostIt.COLORES_CHOICES,
        "usuarios": (
            _usuarios_asignables()
            if request.user.is_staff
            else []
        ),
        "propietario_seleccionado": propietario_seleccionado,
        **_contexto_resumen(request.user),
    }

    return render(request, "editar.html", contexto)


@login_required
@require_POST
def eliminar_tarea(request, tarea_id):
    tarea = _obtener_tarea_permitida(
        request.user,
        tarea_id,
        completada=False,
    )

    tarea.delete()

    messages.success(
        request,
        "El tiquet fue eliminado correctamente.",
    )

    return redirect("pizarra")


@login_required
def historial_completadas(request):
    postits_completados = _tareas_permitidas(
        request.user
    ).filter(completada=True)

    contexto = {
        "postits": postits_completados,
        **_contexto_resumen(request.user),
    }

    return render(
        request,
        "completadas.html",
        contexto,
    )


@login_required
def detalle_completada(request, tarea_id):
    tarea = _obtener_tarea_permitida(
        request.user,
        tarea_id,
        completada=True,
    )

    contexto = {
        "tarea": tarea,
        **_contexto_resumen(request.user),
    }

    return render(
        request,
        "detalle.html",
        contexto,
    )