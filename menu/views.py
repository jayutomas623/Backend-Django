from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from rest_framework import viewsets
from .models import Granel, Extra
from .serializers import GranelSerializer, ExtraSerializer, CategorySerializer
from users.permissions import IsPersonal


def get_horario_actual():
    hora = datetime.now().hour
    if 6 <= hora < 11:
        return 'desayuno'
    elif 11 <= hora < 16:
        return 'almuerzo'
    else:
        return 'cena'


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categorias = Category.objects.all()
        return Response(CategorySerializer(categorias, many=True).data)


class ProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        horario  = get_horario_actual()
        productos = Product.objects.filter(
            disponible=True
        ).filter(
            horario__in=[horario, 'todo']
        )
        categoria_id = request.query_params.get('categoria')
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)
        return Response(ProductSerializer(productos, many=True, context={'request': request}).data)
    
class GranelViewSet(viewsets.ModelViewSet):
    queryset = Granel.objects.all()
    serializer_class = GranelSerializer
    permission_classes = [IsPersonal]

class ExtraViewSet(viewsets.ModelViewSet):
    queryset = Extra.objects.all()
    serializer_class = ExtraSerializer
    permission_classes = [IsPersonal]

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsPersonal]

class ProductManageViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsPersonal]