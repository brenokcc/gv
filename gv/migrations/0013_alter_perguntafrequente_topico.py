# Generated by Django 4.1 on 2024-01-11 20:17

import api
from django.db import migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gv', '0012_perguntafrequente_delete_conteudo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perguntafrequente',
            name='topico',
            field=api.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='perguntas_frequentes', to='gv.topico', verbose_name='Tópico'),
        ),
    ]