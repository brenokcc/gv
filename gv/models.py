import os
import time
from openai import OpenAI
from django.db import models
from api.components import Badge, Steps
from api.models import PushSubscription


class Estado(models.Model):
    sigla = models.CharField('Sigla')
    nome = models.CharField('Nome')

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.sigla


class Prioridade(models.Model):
    descricao = models.CharField('Descrição')
    cor = models.CharField('Cor')
    prazo_resposta = models.IntegerField('Prazo para Resposta', help_text='Em horas')

    class Meta:
        verbose_name = 'Prioridade'
        verbose_name_plural = 'Prioridades'

    def __str__(self):
        return self.descricao

    def get_prazo_resposta(self):
        if self.prazo_resposta > 1:
            return '{} horas'.format(self.prazo_resposta)
        return '{} hora'.format(self.prazo_resposta)


class Assunto(models.Model):
    descricao = models.CharField('Descrição')

    class Meta:
        verbose_name = 'Assunto'
        verbose_name_plural = 'Assuntos'

    def __str__(self):
        return self.descricao

    def get_qtd_topicos(self):
        return self.topicos.count()
    

class Topico(models.Model):
    assunto = models.ForeignKey(Assunto, verbose_name='Assunto', related_name='topicos')
    descricao = models.CharField('Descrição')
    codigo_openai = models.CharField('Código', null=True, blank=True)

    class Meta:
        verbose_name = 'Tópico'
        verbose_name_plural = 'Tópicos'

    def __str__(self):
        return '{} - {}'.format(self.assunto, self.descricao)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.codigo_openai is None:
            client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
            assistant = client.beta.assistants.create(
                name='AnalisaRN {} - {}'.format(self.assunto, self.descricao),
                instructions="",
                tools=[{"type": "retrieval"}],
                model="gpt-3.5-turbo-1106"
            )
            Topico.objects.filter(pk=self.pk).update(codigo_openai=assistant.id)

    def perguntar_inteligencia_artificial(self, pergunta):
        client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
        assistant = client.beta.assistants.retrieve(self.codigo_openai)
        thread = client.beta.threads.create()
        file_ids = list(self.arquivos.values_list('codigo_openai', flat=True))
        message = client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=pergunta, file_ids=file_ids
        )
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
        while run.status != 'completed':
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        breakpoint()
        return messages.data[0].content[0].text.value#.replace('【9†source】', '')


class Arquivo(models.Model):
    topico = models.ForeignKey(Topico, verbose_name='Tópico', related_name='arquivos', null=True)
    nome = models.CharField('Nome')
    arquivo = models.FileField('Arquivo', upload_to='arquivos', null=True)
    codigo_openai = models.CharField('Código', null=True, blank=True)

    class Meta:
        verbose_name = 'Arquivo'
        verbose_name_plural = 'Arquivos'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.codigo_openai is None:
            client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
            with open(self.arquivo.path, 'rb') as file:
                uploaded_file = client.files.create(file=file, purpose='assistants')
                assistant_file = client.beta.assistants.files.create(
                    assistant_id=self.topico.codigo_openai, file_id=uploaded_file.id
                )
                Arquivo.objects.filter(pk=self.pk).update(codigo_openai=assistant_file.id)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.codigo_openai:
            client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
            client.beta.assistants.files.delete(
                file_id=self.codigo_openai, assistant_id=self.topico.codigo_openai
            )
            client.files.delete(self.codigo_openai)


class PerguntaFrequente(models.Model):
    topico = models.ForeignKey(Topico, verbose_name='Tópico', related_name='perguntas_frequentes')
    pergunta = models.CharField('Pergunta')
    resposta = models.TextField('Resposta', blank=True)

    class Meta:
        verbose_name = 'Pergunta Frequente'
        verbose_name_plural = 'Perguntas Frequentes'

    def __str__(self):
        return self.descricao
    
    def save(self, *args, **kwargs):
        if not self.resposta and self.topico.arquivos.exists():
            self.resposta = self.topico.perguntar_inteligencia_artificial(self.pergunta)
        super().save(*args, **kwargs)


class Especialista(models.Model):
    cpf = models.CharField('CPF')
    nome = models.CharField('Nome')
    registro = models.CharField('Nº do Registro Profissional', null=True, blank=True)
    minicurriculo = models.TextField('Minicurrículo', null=True, blank=True) 
    endereco = models.CharField('Endereço', null=True, blank=True)
    telefone = models.CharField('Telefone', null=True, blank=True)
    email = models.CharField('E-mail', null=True, blank=True)
    estados = models.ManyToManyField(Estado, verbose_name='Estados', pick=True)
    assuntos = models.ManyToManyField(Assunto, verbose_name='Assuntos', pick=True)
    

    class Meta:
        verbose_name = 'Especialista'
        verbose_name_plural = 'Especialistas'

    def __str__(self):
     return '{} ({})'.format(self.nome, self.cpf)


class Cliente(models.Model):
    cpf_cnpj = models.CharField('CPF/CNPJ')
    nome = models.CharField('Nome')
    endereco = models.CharField('Endereço', null=True, blank=True)
    telefone = models.CharField('Telefone')

    cpf_responsavel = models.CharField('CPF do Responsável')
    nome_responsavel = models.CharField('Nome do Responsável')
    cargo_responsavel = models.CharField('Cargo do Responsável')
    email_responsavel = models.EmailField('E-mail', null=True)

    estado = models.ForeignKey(Estado, verbose_name='Estado', null=True)
    assuntos = models.ManyToManyField(Assunto, verbose_name='Assuntos', blank=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return '{} ({})'.format(self.nome, self.cpf_cnpj)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        consultante = Consultante.objects.filter(cpf=self.cpf_responsavel).first()
        if consultante is None:
            consultante = Consultante()
            consultante.cliente = self
            consultante.cpf = self.cpf_responsavel
            consultante.nome = self.nome_responsavel
            consultante.save()

class Consultante(models.Model):
    cliente = models.ForeignKey(Cliente, verbose_name='Cliente', related_name='consultantes')
    cpf = models.CharField('CPF')
    nome = models.CharField('Nome')

    class Meta:
        verbose_name = 'Consultante'
        verbose_name_plural = 'Consultantes'

    def __str__(self):
     return '{} ({})'.format(self.nome, self.cpf)


class ConsultaQuerySet(models.QuerySet):

    def aguardando_especialista(self):
        return self.filter(especialista__isnull=True)

    def aguardando_resposta(self):
        return self.filter(especialista__isnull=False, resposta__isnull=True)

    def aguardando_envio(self):
        return self.filter(resposta__isnull=False, data_resposta__isnull=True)

    def finalizadas(self):
        return self.filter(data_resposta__isnull=False)


class Consulta(models.Model):
    consultante = models.ForeignKey(Consultante, verbose_name='Consultante')
    prioridade = models.ForeignKey(Prioridade, verbose_name='Prioridade')
    topico = models.ForeignKey(Topico, verbose_name='Tópico')
    pergunta = models.TextField(verbose_name='Pergunta')
    data_pergunta = models.DateTimeField('Data da Pergunta', auto_now_add=True)

    especialista = models.ForeignKey(Especialista, verbose_name='Especialista', null=True, blank=True)
    observacao = models.TextField(verbose_name='Observação', null=True, blank=True)
    resposta = models.TextField(verbose_name='Resposta', null=True, blank=True)
    data_resposta = models.DateTimeField('Data da Resposta', null=True, blank=True)

    data_consulta = models.DateTimeField('Data da Consulta', null=True, blank=True)
    pergunta_ia = models.TextField(verbose_name='Pergunta I.A.', null=True, blank=True)
    resposta_ia = models.TextField(verbose_name='Resposta I.A.', null=True, blank=True)

    objects = ConsultaQuerySet()

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'

    def __str__(self):
        return 'Consulta {} ({})'.format(self.pk, self.topico.assunto)

    def get_prioridade(self):
        return Badge(self.prioridade.cor, self.prioridade.descricao)

    def get_passos(self):
        steps = Steps()
        steps.append('Pergunta', self.data_pergunta)
        steps.append('Consulta', self.data_consulta)
        steps.append('Resposta', self.data_resposta)
        return steps

    def save(self, *args, **kwargs):
        pk = self.pk
        if self.pergunta_ia is None:
            self.pergunta_ia = self.pergunta
        if self.resposta is None and self.resposta_ia:
            self.resposta = self.resposta_ia
        super().save(*args, **kwargs)
        if pk is None:
            cpfs = Especialista.objects.filter(assuntos=self.topico.assunto).values_list('cpf', flat=True)
            texto = 'Nova pergunta sobre "{}" cadastrada pelo cliente "{}".'.format(self.topico, self.consultante.cliente)
            for subscription in PushSubscription.objects.filter(user__username__in=cpfs):
                subscription.notify(texto)


class Anexo(models.Model):
    consulta = models.ForeignKey(Consulta, verbose_name='Consulta', related_name='anexos')
    nome = models.CharField('Nome')
    observacao = models.TextField('Observação')
    data_hora = models.DateTimeField(auto_now_add=True)
    arquivo = models.FileField('Arquivo', upload_to='anexos', null=True)

    class Meta:
        verbose_name = 'Anexo'
        verbose_name_plural = 'Anexos'


class Interacao(models.Model):
    consulta = models.ForeignKey(Consulta, verbose_name='Consulta', related_name='interacoes')
    mensagem = models.CharField('Mensagem')
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Interação'
        verbose_name_plural = 'Interações'


class Mensalidade(models.Model):
    cliente = models.ForeignKey(Cliente, verbose_name='Cliente', related_name='mensalidades')
    valor = models.DecimalField(verbose_name='Valor')
    data_vencimento = models.DateField(verbose_name='Data do Vencimento')
    data_pagamento = models.DateField(verbose_name='Data do Pagamento', null=True, blank=True)


    class Meta:
        verbose_name = 'Mensalidade'
        verbose_name_plural = 'Mensalidades'

    def __str__(self):
     return '{} ({}/{})'.format(self.cliente, self.data_vencimento.month, self.data_vencimento.year)
