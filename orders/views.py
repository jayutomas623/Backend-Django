from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, ExtractHour, ExtractWeekDay
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from datetime import timedelta
from .models import Order
from .serializers import CreateOrderSerializer, OrderSerializer
from users.permissions import IsCajero, IsCocina, IsAdmin


# ─────────────────────────────────────────────────────────────────────────────
#  FLUJO BASE
# ─────────────────────────────────────────────────────────────────────────────

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            order = serializer.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, cliente=request.user)
        except Order.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=404)
        return Response(OrderSerializer(order).data)


# ─────────────────────────────────────────────────────────────────────────────
#  MONITOR GENERAL DE PEDIDOS  (todos los roles)
# ─────────────────────────────────────────────────────────────────────────────
#
#  GET  /api/orders/monitor/
#       → Devuelve pedidos activos.
#         - cliente: solo sus propios pedidos
#         - staff  : todos los pedidos activos
#
#  PATCH /api/orders/monitor/<pk>/action/
#       Body: { "action": "confirm_payment"|"start"|"ready"|"deliver"|"cancel",
#               "motivo_cancelacion": "..." (solo para cancel) }
#       Acciones permitidas por rol:
#         cajero → confirm_payment, deliver
#         cocina → start, ready, cancel
#         admin  → todas
# ─────────────────────────────────────────────────────────────────────────────

class MonitorOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        qs   = Order.objects.prefetch_related('items__producto').order_by('creado_en')

        if user.rol == 'cliente':
            qs = qs.filter(
                cliente=user,
                estado__in=['en_espera', 'confirmado', 'en_preparacion', 'listo'],
            )
        else:
            qs = qs.filter(
                estado__in=['en_espera', 'confirmado', 'en_preparacion', 'listo'],
            )

        return Response(OrderSerializer(qs, many=True).data)

    def patch(self, request, pk):
        user   = request.user
        action = request.data.get('action')

        try:
            if user.rol == 'cliente':
                order = Order.objects.get(pk=pk, cliente=user)
            else:
                order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'Pedido no encontrado.'}, status=404)

        # ── Permisos por acción ──────────────────────────────────────────────
        es_cajero = user.rol in ('cajero', 'admin')
        es_cocina = user.rol in ('cocina', 'admin')

        # Cajero: confirmar pago en efectivo
        if action == 'confirm_payment':
            if not es_cajero:
                return Response({'detail': 'Solo el cajero puede confirmar pagos.'}, status=403)
            if order.estado != 'en_espera':
                return Response({'detail': 'Solo se pueden confirmar pedidos en espera.'}, status=400)
            order.estado        = 'en_preparacion'
            order.confirmado_en = timezone.now()
            order.save()

        # Cocina: iniciar preparación
        elif action == 'start':
            if not es_cocina:
                return Response({'detail': 'Solo cocina puede iniciar pedidos.'}, status=403)
            if order.estado != 'confirmado':
                return Response({'detail': 'El pedido debe estar confirmado para iniciar.'}, status=400)
            order.estado = 'en_preparacion'
            order.save()

        # Cocina: marcar listo
        elif action == 'ready':
            if not es_cocina:
                return Response({'detail': 'Solo cocina puede marcar pedidos listos.'}, status=403)
            if order.estado != 'en_preparacion':
                return Response({'detail': 'El pedido debe estar en preparación.'}, status=400)
            order.estado = 'listo'
            order.save()

        # Cajero/mesero: marcar entregado
        elif action == 'deliver':
            if not es_cajero:
                return Response({'detail': 'Solo el cajero puede marcar pedidos entregados.'}, status=403)
            if order.estado != 'listo':
                return Response({'detail': 'El pedido debe estar listo para entregarse.'}, status=400)
            order.estado = 'entregado'
            order.save()

        # Cocina/admin: cancelar
        elif action == 'cancel':
            if not es_cocina:
                return Response({'detail': 'Solo cocina puede cancelar pedidos.'}, status=403)
            if order.estado not in ('en_espera', 'confirmado', 'en_preparacion'):
                return Response({'detail': 'No se puede cancelar un pedido listo o entregado.'}, status=400)
            motivo = request.data.get('motivo_cancelacion', '').strip()
            if not motivo:
                return Response({'detail': 'Debes especificar un motivo de cancelación.'}, status=400)
            order.estado               = 'cancelado'
            order.motivo_cancelacion   = motivo
            order.save()
            # Devolver stock de envasados
            for item in order.items.all():
                if item.producto.tipo == 'envasado':
                    item.producto.stock += item.cantidad
                    item.producto.save()

        else:
            return Response({'detail': f'Acción desconocida: {action}'}, status=400)

        return Response(OrderSerializer(order).data)


# ─────────────────────────────────────────────────────────────────────────────
#  PANEL CAJERO  (vista lista + búsqueda por código)
# ─────────────────────────────────────────────────────────────────────────────

class CashierListView(APIView):
    """Lista de pedidos en efectivo pendientes de pago."""
    permission_classes = [IsCajero]

    def get(self, request):
        orders = Order.objects.filter(
            estado='en_espera',
            metodo_pago='efectivo',
        ).prefetch_related('items__producto').order_by('creado_en')
        return Response(OrderSerializer(orders, many=True).data)


class CashierSearchView(APIView):
    """Búsqueda de pedido por código para el cajero."""
    permission_classes = [IsCajero]

    def get(self, request):
        codigo = request.query_params.get('codigo', '').strip()
        if not codigo:
            return Response({'detail': 'Proporciona ?codigo=...'}, status=400)
        try:
            order = Order.objects.prefetch_related('items__producto').get(codigo=codigo)
        except Order.DoesNotExist:
            return Response({'detail': 'Pedido no encontrado.'}, status=404)
        return Response(OrderSerializer(order).data)


# ─────────────────────────────────────────────────────────────────────────────
#  ENDPOINTS HEREDADOS (compatibilidad con flujos anteriores)
# ─────────────────────────────────────────────────────────────────────────────

class ConfirmPaymentView(APIView):
    """Confirmar pago en efectivo por código UUID (flujo legacy)."""
    permission_classes = [IsCajero]

    def patch(self, request, codigo):
        try:
            order = Order.objects.get(codigo=codigo, estado='en_espera')
        except Order.DoesNotExist:
            return Response({'detail': 'Pedido no encontrado o ya confirmado.'}, status=404)
        order.estado        = 'en_preparacion'
        order.confirmado_en = timezone.now()
        order.save()
        return Response(OrderSerializer(order).data)


class CancelOrderView(APIView):
    permission_classes = [IsCocina]

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, estado='en_espera')
        except Order.DoesNotExist:
            return Response({'detail': 'Pedido no encontrado o ya no está en espera.'}, status=404)
        motivo = request.data.get('motivo_cancelacion')
        if not motivo:
            return Response({'detail': 'Debes especificar un motivo para cancelar.'}, status=400)
        order.estado               = 'cancelado'
        order.motivo_cancelacion   = motivo
        order.save()
        for item in order.items.all():
            if item.producto.tipo == 'envasado':
                item.producto.stock += item.cantidad
                item.producto.save()
        return Response({'detail': 'Pedido cancelado y stock devuelto exitosamente.'})


# ─────────────────────────────────────────────────────────────────────────────
#  SPRINT 4 — ESTADÍSTICAS DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

class DashboardStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        hoy          = timezone.now().date()
        pedidos_hoy  = Order.objects.filter(creado_en__date=hoy)
        ventas_hoy   = (
            pedidos_hoy.filter(estado='entregado')
            .aggregate(total=Sum('total'))['total'] or 0
        )
        from orders.models import OrderItem
        top = (
            OrderItem.objects
            .values('producto__nombre')
            .annotate(total_vendido=Sum('cantidad'))
            .order_by('-total_vendido')
            .first()
        )
        return Response({
            'ventas_hoy':          float(ventas_hoy),
            'pedidos_completados': pedidos_hoy.filter(estado='entregado').count(),
            'pedidos_cancelados':  pedidos_hoy.filter(estado='cancelado').count(),
            'pedidos_activos':     Order.objects.filter(
                estado__in=['en_espera', 'confirmado', 'en_preparacion']
            ).count(),
            'top_producto': top['producto__nombre'] if top else '—',
        })


class WeeklySalesView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        since = timezone.now() - timedelta(days=6)
        data  = (
            Order.objects
            .filter(creado_en__gte=since, estado='entregado')
            .annotate(fecha=TruncDate('creado_en'))
            .values('fecha')
            .annotate(total=Sum('total'), pedidos=Count('id'))
            .order_by('fecha')
        )
        DIAS   = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
        result = []
        for i in range(7):
            day   = (timezone.now() - timedelta(days=6 - i)).date()
            entry = next((d for d in data if d['fecha'] == day), None)
            result.append({
                'dia':     DIAS[day.weekday()],
                'fecha':   str(day),
                'total':   float(entry['total']) if entry else 0,
                'pedidos': entry['pedidos'] if entry else 0,
            })
        return Response(result)


class HeatmapView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        since = timezone.now() - timedelta(weeks=4)
        data  = (
            Order.objects
            .filter(creado_en__gte=since)
            .annotate(hora=ExtractHour('creado_en'), dia_semana=ExtractWeekDay('creado_en'))
            .values('hora', 'dia_semana')
            .annotate(count=Count('id'))
        )
        DIAS   = {1: 6, 2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5}
        return Response([
            {'hora': d['hora'], 'dia': DIAS.get(d['dia_semana'], 0), 'count': d['count']}
            for d in data
        ])


class TopProductsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from orders.models import OrderItem
        top = (
            OrderItem.objects
            .values('producto__nombre', 'producto__precio')
            .annotate(total_vendido=Sum('cantidad'))
            .order_by('-total_vendido')[:5]
        )
        return Response([
            {
                'nombre':        t['producto__nombre'],
                'precio':        float(t['producto__precio']),
                'total_vendido': t['total_vendido'],
            }
            for t in top
        ])