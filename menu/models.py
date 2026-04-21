
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

class Granel(models.Model):
    ESTADO_CHOICES = [
        ('rojo', 'Reposición inmediata'),
        ('amarillo', 'Pronta reposición'),
        ('verde', 'Producto disponible'),
    ]
    nombre = models.CharField(max_length=100)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='verde')

    class Meta:
        db_table = 'granel'

    def __str__(self):
        return self.nombre

class Extra(models.Model):
    ESTADO_CHOICES = [
        ('rojo', 'Reposición inmediata/Agotado'),
        ('amarillo', 'Pronta reposición'),
        ('verde', 'Producto disponible'),
    ]
    nombre = models.CharField(max_length=100)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='verde')

    class Meta:
        db_table = 'extras'

    def __str__(self):
        return self.nombre

class Product(models.Model):
    HORARIO_CHOICES = [
        ('desayuno', 'Desayuno'),
        ('almuerzo', 'Almuerzo'),
        ('cena',     'Cena'),
        ('todo',     'Todo el día'),
    ]
    
    TIPO_CHOICES = [
        ('platillo', 'Platillo Preparado'),
        ('envasado', 'Producto Envasado'),
    ]

    categoria   = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='productos')
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES, default='platillo') # NUEVO
    nombre      = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio      = models.DecimalField(max_digits=8, decimal_places=2)
    imagen      = models.ImageField(upload_to='productos/', null=True, blank=True)
    disponible  = models.BooleanField(default=True)
    horario     = models.CharField(max_length=10, choices=HORARIO_CHOICES, default='todo')

    stock       = models.IntegerField(default=0, null=True, blank=True) # NUEVO
    
    extras_asociados = models.ManyToManyField(Extra, blank=True, related_name='platillos') # NUEVO

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return self.nombre