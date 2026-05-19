import uuid
from django.db import models
from django.conf import settings


class Mesa(models.Model):
    ESTADO_CHOICES = [
        ('libre',     'Libre'),
        ('ocupada',   'Ocupada'),
        ('reservada', 'Reservada'),
    ]
    numero    = models.PositiveIntegerField(unique=True)
    capacidad = models.PositiveIntegerField(default=4)
    estado    = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='libre')
    pos_x     = models.FloatField(default=100)
    pos_y     = models.FloatField(default=100)
    activa    = models.BooleanField(default=True)

    class Meta:
        db_table = 'mesas'
        ordering = ['numero']

    def __str__(self):
        return f'Mesa {self.numero} — {self.get_estado_display()}'


class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente de anticipo'),
        ('confirmada', 'Confirmada'),
        ('activa',     'Activa'),
        ('completada', 'Completada'),
        ('cancelada',  'Cancelada'),
    ]
    mesa            = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='reservas')
    cliente         = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas'
    )
    pedido          = models.OneToOneField(
        'orders.Order', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reserva'
    )
    estado          = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    fecha_reserva   = models.DateTimeField()
    codigo          = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    anticipo_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas           = models.TextField(blank=True)
    creado_en       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservas'
        ordering = ['-creado_en']

    def __str__(self):
        return f'Reserva {str(self.codigo)[:8]} — Mesa {self.mesa.numero}'
