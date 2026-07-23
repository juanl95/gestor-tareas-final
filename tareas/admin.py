from django.contrib import admin
from django.utils.html import format_html

from .models import PostIt


admin.site.site_header = "Administración del Gestor de Tiquets"
admin.site.site_title = "Gestor de Tiquets"
admin.site.index_title = "Panel administrativo"


@admin.register(PostIt)
class PostItAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "propietario_visible",
        "estado_visible",
        "color_visible",
        "creado_el",
    )
    list_filter = ("completada", "color", "creado_el", "propietario")
    search_fields = (
        "titulo",
        "contenido",
        "propietario__username",
        "propietario__first_name",
        "propietario__last_name",
    )
    ordering = ("-creado_el",)
    date_hierarchy = "creado_el"
    list_per_page = 20
    list_select_related = ("propietario",)
    autocomplete_fields = ("propietario",)
    readonly_fields = ("creado_el",)
    actions = ("marcar_completadas", "marcar_pendientes")

    fieldsets = (
        (
            "Información del tiquet",
            {
                "fields": (
                    "titulo",
                    "contenido",
                    "color",
                    "propietario",
                )
            },
        ),
        (
            "Estado y auditoría",
            {
                "fields": (
                    "completada",
                    "creado_el",
                )
            },
        ),
    )

    @admin.display(description="Propietario", ordering="propietario__username")
    def propietario_visible(self, obj):
        if obj.propietario:
            return obj.propietario.get_full_name() or obj.propietario.username
        return "Sin asignar"

    @admin.display(description="Estado", ordering="completada")
    def estado_visible(self, obj):
        if obj.completada:
            return format_html(
                '<strong style="color:#047857;">● Completado</strong>'
            )
        return format_html(
            '<strong style="color:#d97706;">● Pendiente</strong>'
        )

    @admin.display(description="Color", ordering="color")
    def color_visible(self, obj):
        return format_html(
            '<span style="display:inline-block;width:14px;height:14px;'
            'border-radius:50%;background:{};margin-right:8px;'
            'vertical-align:-2px;"></span>{}',
            obj.color,
            obj.get_color_display(),
        )

    @admin.action(description="Marcar seleccionados como completados")
    def marcar_completadas(self, request, queryset):
        actualizados = queryset.update(completada=True)
        self.message_user(
            request,
            f"{actualizados} tiquet(s) marcado(s) como completado(s).",
        )

    @admin.action(description="Marcar seleccionados como pendientes")
    def marcar_pendientes(self, request, queryset):
        actualizados = queryset.update(completada=False)
        self.message_user(
            request,
            f"{actualizados} tiquet(s) marcado(s) como pendiente(s).",
        )
