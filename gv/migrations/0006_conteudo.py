# Generated by Django 4.2.4 on 2023-12-12 15:05

import api
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gv', '0005_mensalidade'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conteudo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', api.CharField(max_length=255, verbose_name='Descrição')),
                ('texto', api.TextField(verbose_name='Texto')),
                ('topico', api.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conteudos', to='gv.topico', verbose_name='Tópico')),
            ],
            options={
                'verbose_name': 'Conteúdo',
                'verbose_name_plural': 'Conteúdos',
            },
            bases=(models.Model, api.ModelMixin),
        ),
    ]
