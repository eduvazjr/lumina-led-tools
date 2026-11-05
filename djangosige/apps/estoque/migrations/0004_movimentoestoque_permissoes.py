# Registra a permissao customizada de consulta de estoque, que estava no Meta
# do modelo mas nunca entrou numa migracao (por isso nao existia no banco).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0003_merge_20170625_1454'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='movimentoestoque',
            options={'permissions': (('consultar_estoque', 'Pode consultar estoque'),), 'verbose_name': 'Movimento de Estoque'},
        ),
    ]
