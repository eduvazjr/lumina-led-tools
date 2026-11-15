from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0007_saida_tipo_pagamento'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemcalendario',
            name='tipo_pagamento',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ajuda_custo', 'Ajuda de Custo'),
                    ('pagamento_fornecedor', 'Pagamento Fornecedor'),
                    ('aluguel', 'Aluguel'),
                    ('reembolso_cliente', 'Reembolso Cliente'),
                    ('reembolso_funcionario', 'Reembolso Funcionário'),
                    ('reembolso_outros', 'Reembolso Outros'),
                ],
                default='',
                max_length=30,
                verbose_name='Tipo de Pagamento',
            ),
        ),
    ]

