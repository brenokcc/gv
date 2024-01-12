import datetime

from api import endpoints
import os
from api.components import Steps, WebConf
from api.models import PushSubscription
import openai


class EnviarEmailAcesso(endpoints.Endpoint):
    email = endpoints.EmailField(label='E-mail')
    
    class Meta:
        icon = 'mail-bulk'
        title = 'Enviar E-mail de Acesso'
        target =  'queryset'

    def post(self):
        email = self.getdata('email')
        user = self.objects('auth.user').filter(email=email).first()
        if user is None:
            raise endpoints.ValidationError('Usuário não cadastrado.')
        user.set_password('123')
        user.save()
        self.objects('api.email').send(email, 'Senha de Acesso', 'Querido(a) cliente, sua senha de acesso ao sistema de consultoria online da AnalisaRN é "{}".'.format('123'))
        self.notify('E-mail enviado com sucesso')

    def check_permission(self):
        return self.user.is_superuser

class VideoChamada(endpoints.Endpoint):

    class Meta:
        icon = 'video'
        title = 'Video Chamada'
        target = 'instance'
        modal = False

    def get(self):
        if self.user.username == self.instance.consultante.cpf:
            receiver = self.instance.especialista.cpf
        if self.user.username == self.instance.especialista.cpf:
            receiver = self.instance.consultante.cpf
        return WebConf(self.user.username, receiver)

    def check_permission(self):
        usernames = [self.instance.consultante.cpf, self.instance.especialista and self.instance.especialista.cpf]
        return self.instance.especialista and self.user.username in usernames


class AssumirConsulta(endpoints.Endpoint):

    class Meta:
        icon = 'user-check'
        title = 'Assumir'
        target = 'instance'

    def post(self):
        self.instance.especialista = self.objects('gv.especialista').get(cpf=self.user.username)
        self.instance.save()
        self.notify()
        texto = 'Seu questionamento sobre "{}" está sendo analisado.'.format(self.instance.topico)
        for subscription in PushSubscription.objects.filter(user__username=self.instance.consultante.cpf):
            subscription.notify(texto)

    def check_permission(self):
        return self.instance.especialista_id is None and self.check_roles('especialista')


class ConsultarInteligenciaArtificial(endpoints.Endpoint):
    class Meta:
        icon = 'robot'
        title = 'Consultar I.A.'
        target = 'instance'
        model = 'gv.consulta'
        fields = 'pergunta_ia',

    def post(self):
        self.instance.data_consulta = datetime.datetime.now()
        self.instance.resposta_ia = self.instance.topico.perguntar_inteligencia_artificial(self.instance.pergunta_ia)
        self.instance.save()
        self.notify()

    def check_permission(self):
        return self.instance.especialista_id and self.instance.data_resposta is None and self.check_roles('especialista')


class EditarResposta(endpoints.Endpoint):

    class Meta:
        icon = 'pencil'
        title = 'Editar Resposta'
        target = 'instance'
        model = 'gv.consulta'
        fields = 'resposta',

    def check_permission(self):
        return self.instance.resposta and self.instance.data_resposta is None and self.check_roles('especialista')


class EnviarResposta(endpoints.Endpoint):

    class Meta:
        icon = 'mail-bulk'
        title = 'Enviar Resposta'
        target = 'instance'
        model = 'gv.consulta'
        fields = 'observacao', 'resposta'

    def check_permission(self):
        return self.instance.resposta and self.instance.data_resposta is None and self.check_roles('especialista')

    def post(self):
        texto = 'Seu questionamento sobre "{}" foi respondido.'.format(self.instance.topico)
        for subscription in PushSubscription.objects.filter(user__username=self.instance.consultante.cpf):
            subscription.notify(texto)
        self.instance.data_resposta = datetime.datetime.now()
        super().post()


class RegistrarPagamento(endpoints.Endpoint):

    class Meta:
        icon = 'dollar'
        title = 'Registrar Pagamento'
        target = 'instance'
        model = 'gv.mensalidade'
        fields = 'data_pagamento',
