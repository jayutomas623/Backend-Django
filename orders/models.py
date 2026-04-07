import uuid
from django.db import models
from django.conf import settings
from menu.models import Product


class Order(models.Model):
    ESTADO_CHOICES = [
        ('en_espera',      'En espera de pago'),
        ('confirmado',     'Confirmado'),
        ('en_preparacion', 'En preparación'),
        ('listo',          'Listo'),
        ('entregado',      'Entregado'),
    ]
    PAGO_CHOICES = [
        ('qr',       'QR'),
        ('efectivo', 'Efectivo'),
    ]

    codigo        = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    cliente       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pedidos')
    estado        = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='en_espera')
    metodo_pago   = models.CharField(max_length=10, choices=PAGO_CHOICES)
    total         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    creado_en     = models.DateTimeField(auto_now_add=True)
    confirmado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'pedidos'
        ordering = ['-creado_en']

    def __str__(self):
        return f'Pedido {str(self.codigo)[:8]} — {self.estado}'


class OrderItem(models.Model):
    pedido          = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    producto        = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad        = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = 'pedido_items'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario