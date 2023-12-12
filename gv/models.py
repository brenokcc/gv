from django.db import models
from api.components import Badge, Steps
from api.models import PushSubscription


class TipoContrato(models.Model):
    descricao = models.CharField('Descrição')

    class Meta:
        verbose_name = 'Tipo de Contrato'
        verbose_name_plural = 'Tipos de Contrato'

    def __str__(self):
        return self.descricao


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

    class Meta:
        verbose_name = 'Tópico'
        verbose_name_plural = 'Tópicos'

    def __str__(self):
        return self.descricao


class Especialista(models.Model):
    cpf = models.CharField('CPF')
    nome = models.CharField('Nome')
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

    tipo_contrato = models.ForeignKey(TipoContrato, verbose_name='Tipo de Contrato')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return '{} ({})'.format(self.nome, self.cpf_cnpj)


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
        return self.filter(resposta__isnull=True)

    def aguardando_envio(self):
        return self.filter(data_resposta__isnull=True)

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
