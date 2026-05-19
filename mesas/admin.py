from django.contrib import admin
from .models import Mesa, Reserva


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display  = ('numero', 'capacidad', 'estado', 'pos_x', 'pos_y', 'activa')
    list_filter   = ('estado', 'activa')
    list_editable = ('estado', 'activa')
    ordering      = ('numero',)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'mesa', 'cliente', 'estado', 'fecha_reserva', 'anticipo_pagado', 'creado_en')
    list_filter   = ('estado',)
    search_fields = ('codigo', 'cliente__email', 'cliente__nombre_completo')
    readonly_fields = ('codigo', 'creado_en')
