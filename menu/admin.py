from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'categoria', 'precio', 'horario', 'disponible')
    list_filter   = ('categoria', 'horario', 'disponible')
    search_fields = ('nombre',)