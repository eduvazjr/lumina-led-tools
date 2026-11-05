# Registra a permissao customizada de faturamento, que estava no Meta do
# modelo mas nunca entrou numa migracao (por isso nao existia no banco).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0002_auto_20170625_1450'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pedidocompra',
            options={'permissions': (('faturar_pedidocompra', 'Pode faturar Pedidos de Compra'),), 'verbose_name': 'Pedido de Compra'},
        ),
    ]
