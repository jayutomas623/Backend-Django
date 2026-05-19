from rest_framework import serializers
from .models import Mesa, Reserva


class MesaSerializer(serializers.ModelSerializer):
    reserva_activa = serializers.SerializerMethodField()

    class Meta:
        model  = Mesa
        fields = ['id', 'numero', 'capacidad', 'estado', 'pos_x', 'pos_y', 'activa', 'reserva_activa']

    def get_reserva_activa(self, obj):
        r = obj.reservas.filter(estado__in=['confirmada', 'activa']).first()
        if r:
            return {
                'id':      r.id,
                'codigo':  str(r.codigo),
                'cliente': r.cliente.nombre_completo,
                'estado':  r.estado,
                'fecha':   r.fecha_reserva.isoformat(),
            }
        return None


class ReservaSerializer(serializers.ModelSerializer):
    mesa_numero    = serializers.IntegerField(source='mesa.numero', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    codigo         = serializers.UUIDField(read_only=True)

    class Meta:
        model  = Reserva
        fields = [
            'id', 'codigo', 'mesa', 'mesa_numero',
            'cliente', 'cliente_nombre',
            'estado', 'fecha_reserva', 'anticipo_pagado', 'notas', 'creado_en',
        ]
        read_only_fields = ['cliente', 'codigo', 'creado_en']

    def create(self, validated_data):
            validated_data['cliente'] = self.context['request'].user
            reserva = super().create(validated_data)
            
            mesa = reserva.mesa
            if mesa.estado == 'libre':
                mesa.estado = 'reservada'
                mesa.save()
                
            return reserva
