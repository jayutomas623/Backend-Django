from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'


class IsCajero(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ('cajero', 'admin')


class IsCocina(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ('cocina', 'admin')


class IsPersonal(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol in ('cajero', 'cocina', 'admin')


class IsCliente(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'cliente'