import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0003_order_motivo_cancelacion_alter_order_estado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Mesa',
            fields=[
                ('id',        models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero',    models.PositiveIntegerField(unique=True)),
                ('capacidad', models.PositiveIntegerField(default=4)),
                ('estado',    models.CharField(
                    choices=[('libre', 'Libre'), ('ocupada', 'Ocupada'), ('reservada', 'Reservada')],
                    default='libre', max_length=10
                )),
                ('pos_x',   models.FloatField(default=100)),
                ('pos_y',   models.FloatField(default=100)),
                ('activa',  models.BooleanField(default=True)),
            ],
            options={'db_table': 'mesas', 'ordering': ['numero']},
        ),
        migrations.CreateModel(
            name='Reserva',
            fields=[
                ('id',              models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado',          models.CharField(
                    choices=[
                        ('pendiente',  'Pendiente de anticipo'),
                        ('confirmada', 'Confirmada'),
                        ('activa',     'Activa'),
                        ('completada', 'Completada'),
                        ('cancelada',  'Cancelada'),
                    ],
                    default='pendiente', max_length=15
                )),
                ('fecha_reserva',   models.DateTimeField()),
                ('codigo',          models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('anticipo_pagado', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('notas',           models.TextField(blank=True)),
                ('creado_en',       models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reservas',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('mesa', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reservas',
                    to='mesas.mesa',
                )),
                ('pedido', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reserva',
                    to='orders.order',
                )),
            ],
            options={'db_table': 'reservas', 'ordering': ['-creado_en']},
        ),
    ]
