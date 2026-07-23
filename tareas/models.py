from django.conf import settings
from django.db import models


class PostIt(models.Model):
    COLORES_CHOICES = [
        ("#2563eb", "Azul profesional"),
        ("#7c3aed", "Morado creativo"),
        ("#059669", "Verde progreso"),
        ("#f97316", "Naranja urgente"),
        ("#e11d48", "Rojo importante"),
    ]

    titulo = models.CharField(max_length=100)
    contenido = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        choices=COLORES_CHOICES,
        default="#2563eb",
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    completada = models.BooleanField(default=False)
    propietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tareas",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-creado_el"]
        verbose_name = "Tiquet"
        verbose_name_plural = "Tiquets"

    def __str__(self):
        return self.titulo
