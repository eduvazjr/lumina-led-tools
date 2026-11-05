# Registra a permissao customizada de faturamento, que estava no Meta do
# modelo mas nunca entrou numa migracao (por isso nao existia no banco).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendas', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pedidovenda',
            options={'permissions': (('faturar_pedidovenda', 'Pode faturar Pedidos de Venda'),), 'verbose_name': 'Pedido de Venda'},
        ),
    ]
