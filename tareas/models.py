from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class PostIt(models.Model):
    IMPORTANCIA_BAJA = "BAJA"
    IMPORTANCIA_MEDIA = "MEDIA"
    IMPORTANCIA_ALTA = "ALTA"
    IMPORTANCIA_URGENTE = "URGENTE"

    IMPORTANCIA_CHOICES = [
        (IMPORTANCIA_BAJA, "Baja"),
        (IMPORTANCIA_MEDIA, "Media"),
        (IMPORTANCIA_ALTA, "Alta"),
        (IMPORTANCIA_URGENTE, "Urgente"),
    ]

    ESTADO_ASIGNADO = "ASIGNADO"
    ESTADO_EN_PROGRESO = "EN_PROGRESO"
    ESTADO_COMPLETADO = "COMPLETADO"
    ESTADO_VENCIDO = "VENCIDO"

    ESTADO_CHOICES = [
        (ESTADO_ASIGNADO, "Asignado"),
        (ESTADO_EN_PROGRESO, "En progreso"),
        (ESTADO_COMPLETADO, "Completado"),
        (ESTADO_VENCIDO, "Vencido"),
    ]

    titulo = models.CharField(max_length=100)
    contenido = models.TextField(blank=True)

    importancia = models.CharField(
        max_length=10,
        choices=IMPORTANCIA_CHOICES,
        default=IMPORTANCIA_MEDIA,
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_ASIGNADO,
    )

    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tiquets_asignados",
        null=True,
        blank=True,
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tiquets_creados",
        null=True,
        blank=True,
    )

    duracion_minutos = models.PositiveIntegerField(
        default=60,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10080),
        ],
        help_text="Tiempo disponible desde que el tiquet inicia. Máximo: 7 días.",
    )

    creado_el = models.DateTimeField(auto_now_add=True)
    aceptado_el = models.DateTimeField(null=True, blank=True)
    vence_el = models.DateTimeField(null=True, blank=True)
    completado_el = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["creado_el", "id"]
        verbose_name = "Tiquet"
        verbose_name_plural = "Tiquets"

    def __str__(self):
        return f"TQ-{self.pk or 0:04d} · {self.titulo}"

    @property
    def color_importancia(self):
        colores = {
            self.IMPORTANCIA_BAJA: "#059669",
            self.IMPORTANCIA_MEDIA: "#2563eb",
            self.IMPORTANCIA_ALTA: "#f97316",
            self.IMPORTANCIA_URGENTE: "#dc2626",
        }
        return colores.get(self.importancia, "#2563eb")

    @property
    def esta_vencido(self):
        if self.estado == self.ESTADO_VENCIDO:
            return True

        return bool(
            self.estado == self.ESTADO_EN_PROGRESO
            and self.vence_el
            and timezone.now() >= self.vence_el
        )

    @property
    def segundos_restantes(self):
        if self.estado != self.ESTADO_EN_PROGRESO or not self.vence_el:
            return 0

        diferencia = self.vence_el - timezone.now()
        return max(0, int(diferencia.total_seconds()))

    def iniciar_contador(self, momento=None):
        """Inicia el tiempo solamente cuando el tiquet está asignado."""
        if self.estado != self.ESTADO_ASIGNADO or not self.asignado_a_id:
            return False

        momento = momento or timezone.now()
        self.estado = self.ESTADO_EN_PROGRESO
        self.aceptado_el = momento
        self.vence_el = momento + timedelta(minutes=self.duracion_minutos)
        self.completado_el = None
        self.save(
            update_fields=[
                "estado",
                "aceptado_el",
                "vence_el",
                "completado_el",
            ]
        )
        return True

    def marcar_vencido_si_corresponde(self, momento=None):
        """Valida el vencimiento en el servidor."""
        momento = momento or timezone.now()

        if (
            self.estado == self.ESTADO_EN_PROGRESO
            and self.vence_el
            and momento >= self.vence_el
        ):
            self.estado = self.ESTADO_VENCIDO
            self.save(update_fields=["estado"])
            return True

        return False
