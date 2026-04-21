from rest_framework import serializers
from .models import Category, Product, Granel, Extra

class GranelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Granel
        fields = '__all__'

class ExtraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Extra
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    extras_asociados = ExtraSerializer(many=True, read_only=True)
    extras_ids = serializers.PrimaryKeyRelatedField(
        queryset=Extra.objects.all(), many=True, write_only=True, source='extras_asociados', required=False
    )

    class Meta:
        model  = Product
        fields = ['id', 'nombre', 'descripcion', 'precio', 'imagen', 'horario', 'categoria', 'tipo', 'stock', 'extras_asociados', 'extras_ids']

    def validate_extras_ids(self, extras):
        for extra in extras:
            if extra.estado == 'rojo':
                raise serializers.ValidationError(f"El extra '{extra.nombre}' está agotado y no puede asociarse.")
        return extras

class CategorySerializer(serializers.ModelSerializer):
    productos = ProductSerializer(many=True, read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'nombre', 'descripcion', 'productos']