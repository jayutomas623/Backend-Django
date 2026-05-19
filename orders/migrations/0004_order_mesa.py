import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_motivo_cancelacion_alter_order_estado'),
        ('mesas',  '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='mesa',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pedidos',
                to='mesas.mesa',
            ),
        ),
    ]
