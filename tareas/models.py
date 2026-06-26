from django.db import models

# Definimos la clase que representará nuestra tabla en la base de datos
class PostIt(models.Model):
    
    # Lista de opciones de colores (Código de color HEX, Nombre visible)
    # Esto servirá para que cada post-it tenga un color de fondo CSS diferente
    COLORES_CHOICES = [
        ('#2563eb', 'Azul profesional'),
        ('#7c3aed', 'Morado creativo'),
        ('#059669', 'Verde progreso'),
        ('#f97316', 'Naranja urgente'),
        ('#e11d48', 'Rojo importante'),
    ]

    # Campo de texto corto para el título de la tarea (Máximo 100 caracteres)
    titulo = models.CharField(max_length=100)
    
    # Campo de texto largo para los detalles. 'blank=True' permite que se guarde vacío
    contenido = models.TextField(blank=True)
    
    # Campo para almacenar el color seleccionado. Por defecto será Amarillo ('#fff740')
    color = models.CharField(max_length=7, choices=COLORES_CHOICES, default='#2563eb')
    
    # Almacena la fecha y hora exacta en la que se crea la nota automáticamente
    creado_el = models.DateTimeField(auto_now_add=True)

    # True si ya se completó, False si sigue pendiente en la pizarra
    completada = models.BooleanField(default=False)

    # Este método le dice a Django cómo mostrar el objeto en texto (ej. en el panel de administración)
    def __str__(self):
        return self.titulo