import datetime

from api import endpoints
import os
from api.components import Steps
import openai


class AssumirConsulta(endpoints.Endpoint):

    class Meta:
        icon = 'user-check'
        title = 'Assumir'
        target = 'instance'

    def post(self):
        self.instance.especialista = self.objects('gv.especialista').get(cpf=self.user.username)
        self.instance.save()
        self.notify()

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
        openai.api_key = os.environ.get('CHATGBT_TOKEN')
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{"role": "user", "content": self.instance.pergunta_ia}],
            temperature=0, max_tokens=150
        )
        self.instance.data_consulta = datetime.datetime.now()
        self.instance.resposta_ia = response['choices'][0]['message']['content']
        self.instance.save()
        self.notify()

    def check_permission(self):
        return self.instance.especialista_id and self.instance.resposta is None and self.check_roles('especialista')


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
        fields = 'observacao',

    def check_permission(self):
        return self.instance.resposta and self.instance.data_resposta is None and self.check_roles('especialista')

    def post(self):
        self.instance.data_resposta = datetime.datetime.now()
        super().post()


class RegistrarPagamento(endpoints.Endpoint):

    class Meta:
        icon = 'dollar'
        title = 'Registrar Pagamento'
        target = 'instance'
        model = 'gv.mensalidade'
        fields = 'data_pagamento',
