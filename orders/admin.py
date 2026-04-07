from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    extra  = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'cliente', 'estado', 'metodo_pago', 'total', 'creado_en')
    list_filter   = ('estado', 'metodo_pago')
    search_fields = ('codigo', 'cliente__email')
    inlines       = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'producto', 'cantidad', 'precio_unitario')