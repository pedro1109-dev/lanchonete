"""Modelo de domínio. Preços e consumo da venda são snapshots históricos.
Regras entre várias linhas são centralizadas em services.py e formulários do admin.
"""
from decimal import Decimal
from django.db import models
from django.db.models import Q, F
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


def dinheiro(texto, default=0):
    return models.DecimalField(max_digits=10, decimal_places=2, default=default,
        validators=[MinValueValidator(0)], help_text=texto)

def quantidade(texto):
    return models.DecimalField(max_digits=12, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))], help_text=texto)

def fk(model, texto, **kw):
    return models.ForeignKey(model, on_delete=models.PROTECT, help_text=texto, **kw)

class Nome(models.Model):
    nome = models.CharField(max_length=120, help_text='Nome para identificação e exibição.')
    class Meta:
        abstract = True
    def __str__(self): return self.nome

class Cliente(Nome):
    contato = models.CharField(max_length=120, help_text='Telefone ou e-mail para contato.')

class Mesa(models.Model):
    numero = models.PositiveSmallIntegerField(unique=True, validators=[MinValueValidator(1)], help_text='Número único da mesa no salão.')
    def __str__(self): return f'Mesa {self.numero}'

class Cargo(Nome):
    codigo = models.CharField(max_length=20, unique=True, choices=[(x,x) for x in ['ATENDENTE','COZINHEIRO','ENTREGADOR','GERENTE']], help_text='Função operacional.')

class Funcionario(Nome):
    contato = models.CharField(max_length=120, help_text='Contato do funcionário.')
    ativo = models.BooleanField(default=True, help_text='Disponível para novos atendimentos.')

class ExercicioCargo(models.Model):
    funcionario = fk(Funcionario,'Pessoa que exerce a função.',related_name='exercicios')
    cargo = fk(Cargo,'Cargo exercido no intervalo.')
    inicio = models.DateTimeField(help_text='Início inclusivo do período.')
    fim = models.DateTimeField(null=True,blank=True,help_text='Fim exclusivo; vazio indica período aberto.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(fim__isnull=True)|Q(fim__gt=F('inicio')),name='periodo_cargo_valido'),models.UniqueConstraint(fields=['funcionario','cargo','inicio'],name='exercicio_unico')]
    def clean(self):
        qs=ExercicioCargo.objects.filter(funcionario_id=self.funcionario_id,cargo_id=self.cargo_id).exclude(pk=self.pk)
        if self.fim: qs=qs.filter(inicio__lt=self.fim)
        if self.inicio and qs.filter(Q(fim__isnull=True)|Q(fim__gt=self.inicio)).exists():
            raise ValidationError('Períodos da mesma pessoa e função não podem se sobrepor.')
    def __str__(self): return f'{self.funcionario} / {self.cargo}'

class Fornecedor(Nome):
    contato=models.CharField(max_length=120,help_text='Telefone ou e-mail comercial.')

class Ingrediente(Nome):
    unidade=models.CharField(max_length=3,choices=[('kg','Quilo'),('l','Litro'),('un','Unidade')],help_text='Unidade usada no saldo e nas receitas.')
    estoque=models.DecimalField(max_digits=12,decimal_places=3,default=0,validators=[MinValueValidator(0)],help_text='Saldo informado pelo responsável; consumo é estimado, sem baixa automática.')
    fornecedor=fk(Fornecedor,'Fornecedor responsável pelo abastecimento.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(estoque__gte=0),name='estoque_nao_negativo')]

class Categoria(Nome): pass

class Produto(Nome):
    categoria=fk(Categoria,'Categoria do cardápio.')
    preco_base=dinheiro('Preço individual ou promocional do combo.')
    combo=models.BooleanField(default=False,help_text='Se verdadeiro, composição vem de ComponenteCombo.')
    ativo=models.BooleanField(default=True,help_text='Disponível no cardápio; venda valida a composição.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(preco_base__gte=0),name='preco_produto_valido')]
    def clean(self):
        if self.pk and Produto.objects.filter(pk=self.pk).exclude(combo=self.combo).exists():
            raise ValidationError('Não altere o tipo de produto existente; cadastre outro produto.')

class Receita(models.Model):
    produto=fk(Produto,'Produto simples preparado.',related_name='receita')
    ingrediente=fk(Ingrediente,'Insumo utilizado.')
    quantidade=quantidade('Quantidade por unidade do produto, na unidade do insumo.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['produto','ingrediente'],name='receita_unica'),models.CheckConstraint(condition=Q(quantidade__gt=0),name='receita_qtd_positiva')]
    def clean(self):
        if self.produto_id and self.produto.combo: raise ValidationError('Combo usa componentes, não receita direta.')

class ComponenteCombo(models.Model):
    combo=fk(Produto,'Combo que reúne os produtos.',related_name='componentes',limit_choices_to={'combo':True})
    produto=fk(Produto,'Produto simples componente.',related_name='em_combos',limit_choices_to={'combo':False})
    quantidade=models.PositiveSmallIntegerField(default=1,validators=[MinValueValidator(1)],help_text='Unidades do produto em um combo.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['combo','produto'],name='componente_unico'),models.CheckConstraint(condition=~Q(combo=F('produto')),name='combo_sem_autorreferencia'),models.CheckConstraint(condition=Q(quantidade__gt=0),name='componente_qtd_positiva')]
    def clean(self):
        if self.combo_id and not self.combo.combo: raise ValidationError('O agrupador deve ser um combo.')
        if self.produto_id and self.produto.combo: raise ValidationError('Combos aninhados não são permitidos.')

class Variacao(Nome):
    produto=fk(Produto,'Produto ou combo que aceita esta opção.',related_name='variacoes')
    grupo=models.CharField(max_length=60,help_text='Ex.: tamanho ou ponto. Escolhe-se no máximo uma opção por grupo.')
    acrescimo=dinheiro('Acréscimo por unidade vendida.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['produto','grupo','nome'],name='variacao_unica'),models.CheckConstraint(condition=Q(acrescimo__gte=0),name='variacao_preco_valido')]

class Adicional(Nome):
    preco=dinheiro('Preço por unidade adicional.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(preco__gte=0),name='adicional_preco_valido')]

class ProdutoAdicional(models.Model):
    produto=fk(Produto,'Produto ou combo compatível.',related_name='adicionais_permitidos')
    adicional=fk(Adicional,'Adicional permitido.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['produto','adicional'],name='adicional_permitido_unico')]

class ReceitaAdicional(models.Model):
    adicional=fk(Adicional,'Adicional preparado.',related_name='receita')
    ingrediente=fk(Ingrediente,'Ingrediente do adicional.')
    quantidade=quantidade('Quantidade por unidade adicional.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['adicional','ingrediente'],name='receita_adicional_unica'),models.CheckConstraint(condition=Q(quantidade__gt=0),name='receita_adicional_qtd')]

class Promocao(Nome):
    inicio=models.DateTimeField(help_text='Início inclusivo da promoção.')
    fim=models.DateTimeField(help_text='Fim exclusivo da promoção.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(fim__gt=F('inicio')),name='periodo_promocao_valido')]

class PromocaoProduto(models.Model):
    promocao=fk(Promocao,'Campanha promocional.')
    produto=fk(Produto,'Produto ou combo promocionado.',related_name='promocoes')
    preco=dinheiro('Preço temporário. Entre campanhas simultâneas usa-se o menor preço.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['promocao','produto'],name='promocao_produto_unico'),models.CheckConstraint(condition=Q(preco__gte=0),name='promocao_preco_valido')]

class Cupom(models.Model):
    codigo=models.CharField(max_length=30,unique=True,help_text='Código único; comparação exata.')
    tipo=models.CharField(max_length=10,choices=[('VALOR','Valor'),('PERCENTUAL','Percentual')],help_text='Unidade do desconto.')
    valor=dinheiro('Valor em reais ou percentual de 0 a 100.')
    inicio=models.DateTimeField(help_text='Início inclusivo da validade.')
    fim=models.DateTimeField(help_text='Fim exclusivo da validade.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(fim__gt=F('inicio')),name='cupom_periodo_valido'),models.CheckConstraint(condition=Q(valor__gt=0)&(Q(tipo='VALOR')|Q(tipo='PERCENTUAL',valor__lte=100)),name='cupom_valor_valido')]
    def __str__(self): return self.codigo

STATUS=[(x,x.replace('_',' ').title()) for x in ['RECEBIDO','EM_PREPARO','PRONTO','SAIU_ENTREGA','CONCLUIDO','CANCELADO']]
class Pedido(models.Model):
    cliente=fk(Cliente,'Cliente; obrigatório no aplicativo, delivery e uso de cupom.',null=True,blank=True,related_name='pedidos')
    atendente=fk(Funcionario,'Atendente responsável pelo recebimento.',related_name='pedidos_recebidos')
    mesa=fk(Mesa,'Mesa obrigatória somente para consumo local.',null=True,blank=True)
    canal=models.CharField(max_length=10,choices=[('BALCAO','Balcão'),('TELEFONE','Telefone'),('APP','Aplicativo')],help_text='Origem do pedido.')
    modalidade=models.CharField(max_length=10,choices=[('LOCAL','No local'),('RETIRADA','Retirada'),('DELIVERY','Delivery')],help_text='Forma de atendimento.')
    criado_em=models.DateTimeField(default=timezone.now,help_text='Instante em que a venda foi registrada.')
    desconto=dinheiro('Desconto monetário efetivamente concedido sobre os itens.')
    class Meta:
        constraints=[models.CheckConstraint(condition=(Q(modalidade='LOCAL',mesa__isnull=False)|Q(modalidade__in=['RETIRADA','DELIVERY'],mesa__isnull=True)),name='pedido_mesa_modalidade'),models.CheckConstraint(condition=(Q(cliente__isnull=False)|(~Q(canal='APP')&~Q(modalidade='DELIVERY'))),name='pedido_cliente_obrigatorio'),models.CheckConstraint(condition=Q(desconto__gte=0),name='pedido_desconto_valido'),models.CheckConstraint(condition=Q(canal__in=['BALCAO','TELEFONE','APP']),name='pedido_canal_valido')]
        ordering=['-id']
    @property
    def status(self):
        evento=self.historico.order_by('-id').first()
        return evento.status if evento else 'RECEBIDO'
    @property
    def subtotal(self): return sum((i.total for i in self.itens.all()),Decimal('0'))
    @property
    def total(self): return self.subtotal-self.desconto+(self.entrega.taxa if hasattr(self,'entrega') else Decimal('0'))
    def __str__(self): return f'Pedido #{self.pk}'

class ItemPedido(models.Model):
    pedido=fk(Pedido,'Pedido ao qual o item pertence.',related_name='itens')
    produto=fk(Produto,'Produto ou combo vendido.')
    quantidade=models.PositiveSmallIntegerField(validators=[MinValueValidator(1)],help_text='Unidades vendidas.')
    preco_base=dinheiro('Preço base da venda, já considerando promoção; snapshot.')
    promocao=fk(Promocao,'Promoção aplicada na venda.',null=True,blank=True)
    observacao=models.CharField(max_length=300,blank=True,help_text='Instrução de preparo, ex.: sem cebola.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(quantidade__gt=0),name='item_quantidade_positiva'),models.CheckConstraint(condition=Q(preco_base__gte=0),name='item_preco_valido')]
    @property
    def unitario(self): return self.preco_base+sum((v.acrescimo for v in self.variacoes.all()),Decimal('0'))+sum((a.preco*a.quantidade for a in self.adicionais.all()),Decimal('0'))
    @property
    def total(self): return self.unitario*self.quantidade

class ItemVariacao(models.Model):
    item=fk(ItemPedido,'Item personalizado.',related_name='variacoes')
    variacao=fk(Variacao,'Opção selecionada.')
    acrescimo=dinheiro('Acréscimo congelado no instante da venda.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['item','variacao'],name='item_variacao_unica'),models.CheckConstraint(condition=Q(acrescimo__gte=0),name='item_variacao_preco')]

class ItemAdicional(models.Model):
    item=fk(ItemPedido,'Item com adicional.',related_name='adicionais')
    adicional=fk(Adicional,'Adicional selecionado.')
    quantidade=models.PositiveSmallIntegerField(default=1,validators=[MinValueValidator(1)],help_text='Unidades adicionais para cada unidade do item.')
    preco=dinheiro('Preço unitário do adicional na venda; snapshot.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['item','adicional'],name='item_adicional_unico'),models.CheckConstraint(condition=Q(quantidade__gt=0),name='item_adicional_qtd'),models.CheckConstraint(condition=Q(preco__gte=0),name='item_adicional_preco')]

class ConsumoItem(models.Model):
    item=fk(ItemPedido,'Item vendido.',related_name='consumos')
    ingrediente=fk(Ingrediente,'Ingrediente estimado.')
    quantidade=quantidade('Consumo total deste item, incluindo quantidade vendida, combo e adicionais; snapshot.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['item','ingrediente'],name='consumo_item_unico'),models.CheckConstraint(condition=Q(quantidade__gt=0),name='consumo_item_qtd')]

class FormaPagamento(Nome): pass

class Pagamento(models.Model):
    pedido=fk(Pedido,'Pedido pago.',related_name='pagamentos')
    forma=fk(FormaPagamento,'Forma de pagamento utilizada.')
    valor=dinheiro('Valor efetivamente recebido nesta forma; sem troco.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(valor__gt=0),name='pagamento_positivo'),models.UniqueConstraint(fields=['pedido','forma'],name='pagamento_forma_unica')]

class HistoricoStatus(models.Model):
    pedido=fk(Pedido,'Pedido que mudou de etapa.',related_name='historico')
    status=models.CharField(max_length=15,choices=STATUS,help_text='Etapa registrada nesta transição.')
    ocorrido_em=models.DateTimeField(default=timezone.now,help_text='Instante da transição.')
    class Meta:
        ordering=['id']
        constraints=[models.CheckConstraint(condition=Q(status__in=[s[0] for s in STATUS]),name='historico_status_valido')]

class UsoCupom(models.Model):
    pedido=models.OneToOneField(Pedido,on_delete=models.PROTECT,related_name='uso_cupom',help_text='Pedido beneficiado; no máximo um cupom.')
    cupom=fk(Cupom,'Cupom usado.')
    cliente=fk(Cliente,'Cliente que resgatou o cupom.')
    class Meta:
        constraints=[models.UniqueConstraint(fields=['cupom','cliente'],name='cupom_uma_vez_cliente')]

class Entrega(models.Model):
    pedido=models.OneToOneField(Pedido,on_delete=models.PROTECT,related_name='entrega',help_text='Pedido de delivery; uma única entrega.')
    entregador=fk(Funcionario,'Funcionário com cargo de entregador na venda.',related_name='entregas')
    logradouro=models.CharField(max_length=150,help_text='Rua/avenida no momento do pedido.')
    numero=models.CharField(max_length=15,help_text='Número do imóvel, ou s/n.')
    complemento=models.CharField(max_length=100,blank=True,help_text='Apartamento ou referência opcional.')
    bairro=models.CharField(max_length=80,help_text='Bairro de entrega.')
    cidade=models.CharField(max_length=80,help_text='Município de entrega.')
    cep=models.CharField(max_length=9,help_text='CEP do destino.')
    distancia_km=models.DecimalField(max_digits=6,decimal_places=2,validators=[MinValueValidator(0)],help_text='Distância informada pelo atendente.')
    taxa=dinheiro('Taxa calculada pela política vigente e congelada na venda.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(distancia_km__gte=0)&Q(taxa__gte=0),name='entrega_valores_validos')]

class Avaliacao(models.Model):
    pedido=models.OneToOneField(Pedido,on_delete=models.PROTECT,related_name='avaliacao',help_text='Pedido concluído avaliado.')
    nota=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)],help_text='Nota de 1 a 5.')
    comentario=models.CharField(max_length=500,blank=True,help_text='Comentário opcional do cliente.')
    class Meta:
        constraints=[models.CheckConstraint(condition=Q(nota__gte=1,nota__lte=5),name='avaliacao_nota_valida')]
