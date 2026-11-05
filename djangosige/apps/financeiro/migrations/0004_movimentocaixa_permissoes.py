# Registra a permissao customizada do fluxo de caixa, que estava no Meta do
# modelo mas nunca entrou numa migracao (por isso nao existia no banco).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0003_auto_20170820_1808'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='movimentocaixa',
            options={'permissions': (('acesso_fluxodecaixa', 'Pode acessar o Fluxo de Caixa'),), 'verbose_name': 'Movimento de Caixa'},
        ),
    ]
