from django.shortcuts import render


def error_403(request, exception):
    """
    Se muestra cuando el usuario está autenticado,
    pero no tiene permiso para acceder al recurso.
    """
    return render(
        request,
        "403.html",
        status=403,
    )


def error_404(request, exception):
    """
    Se muestra cuando la página o el registro solicitado
    no existe o no está disponible para el usuario.
    """
    return render(
        request,
        "404.html",
        status=404,
    )


def error_500(request):
    """
    Se muestra cuando ocurre un error interno inesperado.
    """
    return render(
        request,
        "500.html",
        status=500,
    )