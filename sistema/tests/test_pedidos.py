import os
from copy import deepcopy
from decimal import Decimal
from datetime import timedelta
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import *
from core.services import criar_pedido, mudar_status, avaliar

class FluxoPedidoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        os.environ['ADMIN_PASSWORD']='Teste-local-123!'
        call_command('seed_demo',verbosity=0)
    def setUp(self):
        self.burger=Produto.objects.get(nome='Burger da casa')
        self.combo=Produto.objects.get(combo=True)
        self.cliente=Cliente.objects.first()
        self.forma=FormaPagamento.objects.get(nome='Pix')
        self.atendente=Funcionario.objects.get(nome__startswith='Ana')
        self.entregador=Funcionario.objects.get(nome__startswith='Leo')
        self.dados={'canal':'BALCAO','modalidade':'RETIRADA','atendente':self.atendente.id,'itens':[{'produto':self.burger.id,'quantidade':1}],'pagamentos':[{'forma':self.forma.id,'valor':'25.00'}]}
    def test_balcao_anonimo_historico(self):
        p=criar_pedido(self.dados)
        self.assertIsNone(p.cliente);self.assertEqual(p.total,25);self.assertEqual(p.status,'RECEBIDO')
        mudar_status(p.id,'EM_PREPARO');mudar_status(p.id,'PRONTO');mudar_status(p.id,'CONCLUIDO')
        self.assertEqual(p.historico.count(),4)
        with self.assertRaises(ValidationError):mudar_status(p.id,'RECEBIDO')
    def test_pagamentos_divididos(self):
        self.dados['pagamentos']=[{'forma':self.forma.id,'valor':'10'},{'forma':FormaPagamento.objects.get(nome='Dinheiro').id,'valor':'15'}]
        self.assertEqual(criar_pedido(self.dados).pagamentos.count(),2)
    def test_pagamento_incorreto_rollback(self):
        self.dados['pagamentos'][0]['valor']='24.99'
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
        self.assertEqual(Pedido.objects.count(),0);self.assertEqual(ItemPedido.objects.count(),0);self.assertEqual(ConsumoItem.objects.count(),0)
    def test_aplicativo_exige_cliente(self):
        self.dados['canal']='APP'
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_mesa_somente_local(self):
        self.dados['modalidade']='LOCAL'
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
        self.dados['mesa']=Mesa.objects.first().id
        self.assertIsNotNone(criar_pedido(self.dados).mesa)
    def test_retirada_rejeita_mesa(self):
        self.dados['mesa']=Mesa.objects.first().id
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_combo_receita_adicional_snapshot(self):
        a=Adicional.objects.first()
        self.dados['itens']=[{'produto':self.combo.id,'quantidade':2,'adicionais':[{'adicional':a.id,'quantidade':2}]}]
        self.dados['pagamentos'][0]['valor']='76'
        p=criar_pedido(self.dados)
        self.assertEqual(p.total,76)
        self.assertEqual(p.itens.first().consumos.get(ingrediente__nome='Bacon').quantidade,Decimal('.160'))
        self.assertEqual(p.itens.first().consumos.get(ingrediente__nome='Suco').quantidade,Decimal('.600'))
        self.combo.preco_base=99;self.combo.save();a.preco=50;a.save()
        self.assertEqual(Pedido.objects.get(pk=p.id).total,76)
    def test_combo_incompleto_rejeitado(self):
        self.combo.componentes.first().delete()
        self.dados['itens'][0]['produto']=self.combo.id
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_cupom_unico_cliente(self):
        self.dados.update(cliente=self.cliente.id,cupom='BEMVINDO10');self.dados['pagamentos'][0]['valor']='22.50'
        p=criar_pedido(self.dados);self.assertEqual(p.desconto,Decimal('2.50'))
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
        self.assertEqual(Pedido.objects.count(),1)
    def test_cupom_expirado(self):
        c=Cupom.objects.first();c.inicio=timezone.now()-timedelta(days=3);c.fim=timezone.now()-timedelta(days=1);c.save()
        self.dados.update(cliente=self.cliente.id,cupom=c.codigo)
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_promocao_preco_congelado(self):
        batata=Produto.objects.get(nome='Batata crocante');self.dados['itens'][0]['produto']=batata.id;self.dados['pagamentos'][0]['valor']='10'
        p=criar_pedido(self.dados);PromocaoProduto.objects.update(preco=7)
        self.assertEqual(p.total,10);self.assertIsNotNone(p.itens.first().promocao)
    def test_variacao_incompativel(self):
        self.dados['itens'][0]['produto']=self.combo.id
        self.dados['itens'][0]['variacoes']=[Variacao.objects.first().id]
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_duas_variacoes_mesmo_grupo(self):
        self.dados['itens'][0]['variacoes']=list(Variacao.objects.values_list('id',flat=True))
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_atendente_sem_cargo(self):
        self.dados['atendente']=self.entregador.id
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_delivery_taxa_fluxo(self):
        self.dados.update(canal='APP',modalidade='DELIVERY',cliente=self.cliente.id,entrega={'entregador':self.entregador.id,'distancia_km':'2','logradouro':'Rua Exemplo','numero':'10','bairro':'Centro','cidade':'Indaiatuba','cep':'13330-000'})
        self.dados['pagamentos'][0]['valor']='33'
        p=criar_pedido(self.dados);self.assertEqual(p.entrega.taxa,8)
        mudar_status(p.id,'EM_PREPARO');mudar_status(p.id,'PRONTO')
        with self.assertRaises(ValidationError):mudar_status(p.id,'CONCLUIDO')
        mudar_status(p.id,'SAIU_ENTREGA');mudar_status(p.id,'CONCLUIDO')
        self.assertEqual(p.status,'CONCLUIDO')
    def test_avaliacao_unica_conclusao(self):
        self.dados['cliente']=self.cliente.id;p=criar_pedido(self.dados)
        with self.assertRaises(ValidationError):avaliar(p.id,{'nota':5})
        for s in ['EM_PREPARO','PRONTO','CONCLUIDO']:mudar_status(p.id,s)
        avaliar(p.id,{'nota':5,'comentario':'Muito bom'})
        with self.assertRaises(ValidationError):avaliar(p.id,{'nota':4})
    def test_quantidade_fracionaria_rejeitada(self):
        self.dados['itens'][0]['quantidade']=1.5
        with self.assertRaises(ValidationError):criar_pedido(self.dados)
    def test_api_exige_autenticacao_csrf(self):
        c=Client(enforce_csrf_checks=True)
        self.assertEqual(c.get('/api/catalogo/').status_code,403)
        c.force_login(get_user_model().objects.first())
        self.assertEqual(c.post('/api/pedidos/',self.dados,content_type='application/json').status_code,403)
    def test_relatorio_exclui_cancelado(self):
        p=criar_pedido(self.dados);mudar_status(p.id,'CANCELADO')
        self.client.force_login(get_user_model().objects.first())
        r=self.client.get('/api/relatorio/').json()
        self.assertEqual(r['quantidade_pedidos'],0);self.assertEqual(r['consumo'],[])
    def test_crud_cliente_e_protecao_referencias(self):
        self.client.force_login(get_user_model().objects.first())
        r=self.client.post('/admin/core/cliente/add/',{'nome':'Cliente CRUD','contato':'teste@example.test','_save':'Salvar'})
        self.assertEqual(r.status_code,302)
        c=Cliente.objects.get(nome='Cliente CRUD')
        r=self.client.post(f'/admin/core/cliente/{c.id}/change/',{'nome':'Cliente editado','contato':'novo@example.test','_save':'Salvar'})
        self.assertEqual(r.status_code,302);c.refresh_from_db();self.assertEqual(c.nome,'Cliente editado')
        r=self.client.post(f'/admin/core/cliente/{c.id}/delete/',{'post':'yes'});self.assertEqual(r.status_code,302);self.assertFalse(Cliente.objects.filter(pk=c.id).exists())
        self.dados['cliente']=self.cliente.id;criar_pedido(self.dados)
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):self.cliente.delete()
