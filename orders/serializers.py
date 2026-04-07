from rest_framework import serializers
from .models import Order, OrderItem
from menu.models import Product


class OrderItemInputSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad    = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    metodo_pago = serializers.ChoiceField(choices=['qr', 'efectivo'])
    items       = OrderItemInputSerializer(many=True)

    def create(self, validated_data):
        from django.utils import timezone
        cliente = self.context['request'].user
        metodo  = validated_data['metodo_pago']
        estado  = 'confirmado' if metodo == 'qr' else 'en_espera'
        order   = Order.objects.create(cliente=cliente, metodo_pago=metodo, estado=estado)
        total   = 0
        for item_data in validated_data['items']:
            producto = Product.objects.get(id=item_data['producto_id'])
            OrderItem.objects.create(
                pedido=order,
                producto=producto,
                cantidad=item_data['cantidad'],
                precio_unitario=producto.precio,
            )
            total += producto.precio * item_data['cantidad']
        order.total = total
        if estado == 'confirmado':
            order.confirmado_en = timezone.now()
        order.save()
        return order


class OrderItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    subtotal        = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model  = OrderItem
        fields = ['producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items  = OrderItemSerializer(many=True, read_only=True)
    codigo = serializers.UUIDField(read_only=True)

    class Meta:
        model  = Order
        fields = ['id', 'codigo', 'estado', 'metodo_pago', 'total', 'creado_en', 'items']