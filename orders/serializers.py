from rest_framework import serializers
from .models import Order, OrderItem
from menu.models import Product


class OrderItemInputSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad    = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    metodo_pago = serializers.ChoiceField(choices=['qr', 'efectivo'])
    items       = OrderItemInputSerializer(many=True)
    mesa_id     = serializers.IntegerField(required=False, allow_null=True)

    def create(self, validated_data):
        from django.utils import timezone
        cliente = self.context['request'].user
        metodo  = validated_data['metodo_pago']
        mesa_id = validated_data.get('mesa_id')
        estado  = 'confirmado' if metodo == 'qr' else 'en_espera'

        # Resolver mesa si viene en el request
        mesa = None
        if mesa_id:
            try:
                from mesas.models import Mesa
                mesa = Mesa.objects.get(pk=mesa_id, activa=True)
            except Exception:
                pass

        order = Order.objects.create(
            cliente=cliente,
            metodo_pago=metodo,
            estado=estado,
            mesa=mesa,
        )
        total = 0

        for item_data in validated_data['items']:
            producto = Product.objects.get(id=item_data['producto_id'])
            cantidad = item_data['cantidad']

            if producto.tipo == 'envasado':
                if producto.stock is None or producto.stock < cantidad:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para: {producto.nombre}"
                    )
                producto.stock -= cantidad
                producto.save()

            OrderItem.objects.create(
                pedido=order,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
            )
            total += producto.precio * cantidad

        order.total = total
        if estado == 'confirmado':
            order.confirmado_en = timezone.now()
        order.save()

        # Si hay mesa, marcarla como ocupada
        if mesa:
            mesa.estado = 'ocupada'
            mesa.save()

        return order


class OrderItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_id     = serializers.IntegerField(source='producto.id', read_only=True)
    subtotal        = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model  = OrderItem
        fields = ['producto_id', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items          = OrderItemSerializer(many=True, read_only=True)
    codigo         = serializers.UUIDField(read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    mesa_numero    = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'codigo', 'estado', 'metodo_pago', 'total',
            'creado_en', 'items', 'motivo_cancelacion',
            'cliente_nombre', 'mesa_numero',
        ]

    def get_mesa_numero(self, obj):
        return obj.mesa.numero if obj.mesa else None
