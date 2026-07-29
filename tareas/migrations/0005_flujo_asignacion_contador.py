from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


def convertir_datos_anteriores(apps, schema_editor):
    PostIt = apps.get_model("tareas", "PostIt")

    importancia_por_color = {
        "#059669": "BAJA",
        "#2563eb": "MEDIA",
        "#7c3aed": "MEDIA",
        "#f97316": "ALTA",
        "#e11d48": "URGENTE",
        "#dc2626": "URGENTE",
    }

    for tiquet in PostIt.objects.all().iterator():
        tiquet.importancia = importancia_por_color.get(
            tiquet.color,
            "MEDIA",
        )

        if tiquet.completada:
            tiquet.estado = "COMPLETADO"
            tiquet.completado_el = tiquet.creado_el
        else:
            tiquet.estado = "ASIGNADO"

        tiquet.save(
            update_fields=[
                "importancia",
                "estado",
                "completado_el",
            ]
        )


def restaurar_datos_anteriores(apps, schema_editor):
    PostIt = apps.get_model("tareas", "PostIt")

    color_por_importancia = {
        "BAJA": "#059669",
        "MEDIA": "#2563eb",
        "ALTA": "#f97316",
        "URGENTE": "#e11d48",
    }

    for tiquet in PostIt.objects.all().iterator():
        tiquet.color = color_por_importancia.get(
            tiquet.importancia,
            "#2563eb",
        )
        tiquet.completada = tiquet.estado == "COMPLETADO"

        tiquet.save(
            update_fields=[
                "color",
                "completada",
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "tareas",
            "0004_alter_postit_options_postit_propietario",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="postit",
            old_name="propietario",
            new_name="asignado_a",
        ),

        migrations.AddField(
            model_name="postit",
            name="aceptado_el",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),

        migrations.AddField(
            model_name="postit",
            name="completado_el",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),

        migrations.AddField(
            model_name="postit",
            name="creado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tiquets_creados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        migrations.AddField(
            model_name="postit",
            name="duracion_minutos",
            field=models.PositiveIntegerField(
                default=60,
                help_text=(
                    "Tiempo disponible desde que el tiquet inicia. "
                    "Máximo: 7 días."
                ),
                validators=[
                    MinValueValidator(1),
                    MaxValueValidator(10080),
                ],
            ),
        ),

        migrations.AddField(
            model_name="postit",
            name="estado",
            field=models.CharField(
                choices=[
                    ("ASIGNADO", "Asignado"),
                    ("EN_PROGRESO", "En progreso"),
                    ("COMPLETADO", "Completado"),
                    ("VENCIDO", "Vencido"),
                ],
                default="ASIGNADO",
                max_length=20,
            ),
        ),

        migrations.AddField(
            model_name="postit",
            name="importancia",
            field=models.CharField(
                choices=[
                    ("BAJA", "Baja"),
                    ("MEDIA", "Media"),
                    ("ALTA", "Alta"),
                    ("URGENTE", "Urgente"),
                ],
                default="MEDIA",
                max_length=10,
            ),
        ),

        migrations.AddField(
            model_name="postit",
            name="vence_el",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),

        migrations.RunPython(
            convertir_datos_anteriores,
            restaurar_datos_anteriores,
        ),

        migrations.RemoveField(
            model_name="postit",
            name="color",
        ),

        migrations.RemoveField(
            model_name="postit",
            name="completada",
        ),

        migrations.AlterField(
            model_name="postit",
            name="asignado_a",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="tiquets_asignados",
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        migrations.AlterModelOptions(
            name="postit",
            options={
                "ordering": [
                    "creado_el",
                    "id",
                ],
                "verbose_name": "Tiquet",
                "verbose_name_plural": "Tiquets",
            },
        ),
    ]