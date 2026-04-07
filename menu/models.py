from django.db import models


class Category(models.Model):
    nombre      = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    orden       = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'categorias'
        ordering = ['orden']

    def __str__(self):
        return self.nombre


class Product(models.Model):
    HORARIO_CHOICES = [
        ('desayuno', 'Desayuno'),
        ('almuerzo', 'Almuerzo'),
        ('cena',     'Cena'),
        ('todo',     'Todo el día'),
    ]

    categoria   = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='productos')
    nombre      = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio      = models.DecimalField(max_digits=8, decimal_places=2)
    imagen      = models.ImageField(upload_to='productos/', null=True, blank=True)
    disponible  = models.BooleanField(default=True)
    horario     = models.CharField(max_length=10, choices=HORARIO_CHOICES, default='todo')

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return self.nombre