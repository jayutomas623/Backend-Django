from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('email', 'nombre_completo', 'rol', 'is_active')
    list_filter   = ('rol', 'is_active')
    ordering      = ('email',)
    search_fields = ('email', 'nombre_completo')

    fieldsets = (
        (None,          {'fields': ('email', 'password')}),
        ('Información', {'fields': ('nombre_completo', 'telefono', 'fecha_nacimiento', 'sexo', 'rol')}),
        ('Permisos',    {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nombre_completo', 'rol', 'password1', 'password2'),
        }),
    )