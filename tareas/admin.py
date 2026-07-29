from django.contrib import admin
from django.utils.html import format_html

from .models import PostIt


admin.site.site_header = "Administración del Gestor de Tiquets"
admin.site.site_title = "Gestor de Tiquets"
admin.site.index_title = "Panel administrativo"


@admin.register(PostIt)
class PostItAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "titulo",
        "asignado_visible",
        "importancia_visible",
        "estado_visible",
        "duracion_minutos",
        "vence_el",
        "creado_el",
    )
    list_filter = (
        "estado",
        "importancia",
        "asignado_a",
        "creado_el",
    )
    search_fields = (
        "titulo",
        "contenido",
        "asignado_a__username",
        "asignado_a__first_name",
        "asignado_a__last_name",
    )
    ordering = ("creado_el", "id")
    date_hierarchy = "creado_el"
    list_per_page = 25
    list_select_related = ("asignado_a", "creado_por")
    autocomplete_fields = ("asignado_a",)
    readonly_fields = (
        "creado_el",
        "creado_por",
        "aceptado_el",
        "vence_el",
        "completado_el",
    )
    actions = (
        "devolver_a_asignados",
        "marcar_completados",
    )

    fieldsets = (
        (
            "Información del tiquet",
            {
                "fields": (
                    "titulo",
                    "contenido",
                    "importancia",
                    "asignado_a",
                    "duracion_minutos",
                )
            },
        ),
        (
            "Estado y seguimiento",
            {
                "fields": (
                    "estado",
                    "creado_por",
                    "creado_el",
                    "aceptado_el",
                    "vence_el",
                    "completado_el",
                )
            },
        ),
    )

    @admin.display(description="Código", ordering="id")
    def codigo(self, obj):
        return f"TQ-{obj.pk:04d}"

    @admin.display(description="Asignado a", ordering="asignado_a__username")
    def asignado_visible(self, obj):
        if not obj.asignado_a:
            return "Sin asignar"
        return obj.asignado_a.get_full_name() or obj.asignado_a.username

    @admin.display(description="Importancia", ordering="importancia")
    def importancia_visible(self, obj):
        return format_html(
            '<span style="display:inline-block;padding:5px 10px;border-radius:999px;'
            'background:{}18;color:{};font-weight:700;">{}</span>',
            obj.color_importancia,
            obj.color_importancia,
            obj.get_importancia_display(),
        )

    @admin.display(description="Estado", ordering="estado")
    def estado_visible(self, obj):
        colores = {
            PostIt.ESTADO_ASIGNADO: "#64748b",
            PostIt.ESTADO_EN_PROGRESO: "#2563eb",
            PostIt.ESTADO_COMPLETADO: "#059669",
            PostIt.ESTADO_VENCIDO: "#dc2626",
        }
        color = colores.get(obj.estado, "#64748b")
        return format_html(
            '<span style="color:{};font-weight:800;">● {}</span>',
            color,
            obj.get_estado_display(),
        )

    def save_model(self, request, obj, form, change):
        if not obj.creado_por_id:
            obj.creado_por = request.user

        if obj.estado == PostIt.ESTADO_ASIGNADO:
            obj.aceptado_el = None
            obj.vence_el = None
            obj.completado_el = None

        super().save_model(request, obj, form, change)

    @admin.action(description="Devolver seleccionados a la cola de asignados")
    def devolver_a_asignados(self, request, queryset):
        actualizados = queryset.update(
            estado=PostIt.ESTADO_ASIGNADO,
            aceptado_el=None,
            vence_el=None,
            completado_el=None,
        )
        self.message_user(
            request,
            f"{actualizados} tiquet(s) devuelto(s) a la cola.",
        )

    @admin.action(description="Marcar seleccionados como completados")
    def marcar_completados(self, request, queryset):
        from django.utils import timezone

        actualizados = queryset.update(
            estado=PostIt.ESTADO_COMPLETADO,
            completado_el=timezone.now(),
        )
        self.message_user(
            request,
            f"{actualizados} tiquet(s) marcado(s) como completado(s).",
        )
