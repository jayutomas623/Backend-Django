from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import CreateOrderSerializer, OrderSerializer
from users.permissions import IsCajero, IsCocina


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


class ConfirmPaymentView(APIView):
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


class KitchenOrdersView(APIView):
    permission_classes = [IsCocina]

    def get(self, request):
        orders = Order.objects.filter(
            estado__in=['confirmado', 'en_preparacion']
        ).prefetch_related('items__producto').order_by('confirmado_en')
        return Response(OrderSerializer(orders, many=True).data)

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=404)
        order.estado = 'listo'
        order.save()
        return Response(OrderSerializer(order).data)


class CashierOrdersView(APIView):
    permission_classes = [IsCajero]

    def get(self, request):
        codigo = request.query_params.get('codigo')
        if not codigo:
            return Response({'detail': 'Proporciona ?codigo=...'}, status=400)
        try:
            order = Order.objects.get(codigo=codigo)
        except Order.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=404)
        return Response(OrderSerializer(order).data)

    def patch(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, estado='listo')
        except Order.DoesNotExist:
            return Response({'detail': 'No encontrado o no está listo.'}, status=404)
        order.estado = 'entregado'
        order.save()
        return Response(OrderSerializer(order).data)