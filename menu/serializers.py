from rest_framework import serializers
from .models import Category, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = ['id', 'nombre', 'descripcion', 'precio', 'imagen', 'horario', 'categoria']


class CategorySerializer(serializers.ModelSerializer):
    productos = ProductSerializer(many=True, read_only=True)

    class Meta:
        model  = Category
        fields = ['id', 'nombre', 'descripcion', 'productos']