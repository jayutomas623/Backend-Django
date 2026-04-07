from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('cliente',  'Cliente'),
        ('cajero',   'Cajero'),
        ('cocina',   'Cocina'),
        ('admin',    'Administrador'),
    ]

    email            = models.EmailField(unique=True)
    nombre_completo  = models.CharField(max_length=150)
    telefono         = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo             = models.CharField(max_length=1, choices=[('M','Masculino'),('F','Femenino'),('O','Otro')], blank=True)
    rol              = models.CharField(max_length=10, choices=ROL_CHOICES, default='cliente')
    is_active        = models.BooleanField(default=True)
    is_staff         = models.BooleanField(default=False)
    date_joined      = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nombre_completo']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuarios'

    def __str__(self):
        return f'{self.nombre_completo} ({self.rol})'