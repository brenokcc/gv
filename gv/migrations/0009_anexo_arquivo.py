# Generated by Django 4.1 on 2024-01-06 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gv', '0008_interacao_anexo'),
    ]

    operations = [
        migrations.AddField(
            model_name='anexo',
            name='arquivo',
            field=models.FileField(null=True, upload_to='anexos', verbose_name='Arquivo'),
        ),
    ]
