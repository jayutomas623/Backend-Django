# C:\Jayu\Sistemas\Proyecto-Django\backend\users\views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .permissions import IsAdmin

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user' : UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user' : UserSerializer(user).data,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({'detail': 'Sesión cerrada correctamente.'})

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
    
class CreateEmployeeView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.rol = request.data.get('rol', 'cliente')
            user.direccion = request.data.get('direccion', '')
            user.ci = request.data.get('ci', '')
            user.save()
            return Response({'detail': 'Empleado creado exitosamente.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- NUEVAS VISTAS DE EMPLEADOS ---
class EmployeeListView(APIView):
    permission_classes = [IsAdmin]
    
    def get(self, request):
        # Excluir clientes, mostrar solo personal
        empleados = User.objects.exclude(rol='cliente').order_by('-date_joined')
        return Response(UserSerializer(empleados, many=True).data)

class EmployeeDetailView(APIView):
    permission_classes = [IsAdmin]
    
    def patch(self, request, pk):
        try:
            empleado = User.objects.get(pk=pk)
            # Alternar estado activo/inactivo (vacaciones, suspensión)
            if 'is_active' in request.data:
                empleado.is_active = request.data['is_active']
            empleado.save()
            return Response(UserSerializer(empleado).data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            empleado = User.objects.get(pk=pk)
            empleado.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)