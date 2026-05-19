from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Mesa, Reserva
from .serializers import MesaSerializer, ReservaSerializer
from users.permissions import IsAdmin, IsPersonal


class MesaViewSet(viewsets.ModelViewSet):
    queryset         = Mesa.objects.filter(activa=True).order_by('numero')
    serializer_class = MesaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsPersonal()]

    # ── Cambiar estado (solo staff) ─────────────────────────────────────────
    @action(detail=True, methods=['patch'], permission_classes=[IsPersonal], url_path='set_estado')
    def set_estado(self, request, pk=None):
        mesa   = self.get_object()
        estado = request.data.get('estado')
        if estado not in dict(Mesa.ESTADO_CHOICES):
            return Response({'detail': 'Estado inválido.'}, status=400)
        mesa.estado = estado
        mesa.save()
        return Response(MesaSerializer(mesa).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated], url_path='liberar')
    def liberar(self, request, pk=None):
        mesa = self.get_object()
        user = request.user

        # Staff libera sin restricciones
        if user.rol in ('cajero', 'cocina', 'admin'):
            mesa.estado = 'libre'
            mesa.save()
            return Response(MesaSerializer(mesa).data)

        # Cliente: verificar que tiene un pedido en esta mesa
        from orders.models import Order
        tiene_pedido = Order.objects.filter(
            mesa=mesa,
            cliente=user,
            estado__in=['confirmado', 'en_preparacion', 'listo', 'entregado'],
        ).exists()

        if not tiene_pedido:
            return Response(
                {'detail': 'Solo puedes liberar una mesa en la que tengas un pedido.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        mesa.estado = 'libre'
        mesa.save()
        return Response(MesaSerializer(mesa).data)

    # ── Seed (solo admin) ───────────────────────────────────────────────────
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def seed(self, request):
        """Crea el layout inicial de mesas si no existen."""
        if Mesa.objects.exists():
            return Response({'detail': 'Ya existen mesas en el sistema.'}, status=400)

        layout = [
            {'numero': 1,  'capacidad': 2, 'pos_x': 60,  'pos_y': 60},
            {'numero': 2,  'capacidad': 2, 'pos_x': 210, 'pos_y': 60},
            {'numero': 3,  'capacidad': 4, 'pos_x': 360, 'pos_y': 60},
            {'numero': 4,  'capacidad': 4, 'pos_x': 520, 'pos_y': 60},
            {'numero': 5,  'capacidad': 6, 'pos_x': 60,  'pos_y': 220},
            {'numero': 6,  'capacidad': 6, 'pos_x': 310, 'pos_y': 220},
            {'numero': 7,  'capacidad': 4, 'pos_x': 540, 'pos_y': 220},
            {'numero': 8,  'capacidad': 2, 'pos_x': 60,  'pos_y': 390},
            {'numero': 9,  'capacidad': 4, 'pos_x': 220, 'pos_y': 390},
            {'numero': 10, 'capacidad': 6, 'pos_x': 460, 'pos_y': 390},
        ]
        created = [Mesa.objects.create(**m) for m in layout]
        return Response(
            {'detail': f'{len(created)} mesas creadas correctamente.'},
            status=status.HTTP_201_CREATED,
        )


class ReservaViewSet(viewsets.ModelViewSet):
    serializer_class   = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.rol in ('cajero', 'cocina', 'admin'):
            return Reserva.objects.all().select_related('mesa', 'cliente')
        return Reserva.objects.filter(cliente=user).select_related('mesa')

    @action(detail=True, methods=['patch'], permission_classes=[IsPersonal])
    def confirmar(self, request, pk=None):
        """Activa la reserva y ocupa la mesa cuando el cliente llega."""
        reserva = self.get_object()
        if reserva.estado != 'confirmada':
            return Response({'detail': 'Solo se pueden activar reservas en estado confirmada.'}, status=400)
        reserva.estado = 'activa'
        reserva.mesa.estado = 'ocupada'
        reserva.mesa.save()
        reserva.save()
        return Response(ReservaSerializer(reserva).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def cancelar(self, request, pk=None):
        reserva = self.get_object()
        if reserva.estado in ('completada', 'cancelada'):
            return Response({'detail': 'No se puede cancelar esta reserva.'}, status=400)
        reserva.estado = 'cancelada'
        if reserva.mesa.estado == 'reservada':
            reserva.mesa.estado = 'libre'
            reserva.mesa.save()
        reserva.save()
        return Response(ReservaSerializer(reserva).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsPersonal])
    def completar(self, request, pk=None):
        reserva = self.get_object()
        reserva.estado = 'completada'
        reserva.mesa.estado = 'libre'
        reserva.mesa.save()
        reserva.save()
        return Response(ReservaSerializer(reserva).data)
