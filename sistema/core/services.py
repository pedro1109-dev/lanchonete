from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import *

D=Decimal

def moeda(value):
    try: n=D(str(value))
    except (InvalidOperation, ValueError): raise ValidationError('Valor monetário inválido.')
    if not n.is_finite() or n<0 or n>D('99999999.99'):
        raise ValidationError('Valor fora do intervalo permitido.')
    return n.quantize(D('0.01'),rounding=ROUND_HALF_UP)

def inteiro(value):
    try:
        n=int(value)
        if isinstance(value,bool) or str(n)!=str(value) or not 1<=n<=999:
            raise ValueError
        return n
    except (ValueError,TypeError): raise ValidationError('Quantidade/identificador deve ser um inteiro positivo de até 999.')

def objeto(model, pk):
    try: return model.objects.get(pk=pk)
    except (model.DoesNotExist,ValueError,TypeError): raise ValidationError(f'{model.__name__} inválido.')

def salvar(obj):
    obj.full_clean();obj.save();return obj

def exerce(funcionario, codigo, agora):
    return funcionario.ativo and funcionario.exercicios.filter(cargo__codigo=codigo,inicio__lte=agora).filter(Q(fim__isnull=True)|Q(fim__gt=agora)).exists()

def preco(produto, agora):
    candidatos=list(produto.promocoes.filter(promocao__inicio__lte=agora,promocao__fim__gt=agora).order_by('preco','id'))
    oferta=next((p for p in candidatos if p.preco<produto.preco_base),None)
    return (oferta.preco,oferta.promocao) if oferta else (produto.preco_base,None)

def composicao(produto):
    consumo=defaultdict(Decimal)
    if produto.combo:
        partes=list(produto.componentes.select_related('produto'))
        if len(partes)<2: raise ValidationError('Combo deve reunir pelo menos dois produtos distintos.')
        if any(p.produto.combo for p in partes): raise ValidationError('Combo não pode conter outro combo.')
        for parte in partes:
            for insumo,qtd in composicao(parte.produto).items(): consumo[insumo]+=qtd*parte.quantidade
    else:
        receita=list(produto.receita.all())
        if not receita: raise ValidationError(f'Cadastre a receita de {produto.nome} antes da venda.')
        for r in receita: consumo[r.ingrediente_id]+=r.quantidade
    return consumo

@transaction.atomic
def criar_pedido(dados):
    agora=timezone.now()
    if not isinstance(dados,dict): raise ValidationError('Envie um objeto JSON.')
    itens=dados.get('itens',[])
    if not isinstance(itens,list) or not 1<=len(itens)<=100: raise ValidationError('Pedido deve ter entre 1 e 100 itens.')
    atendente=objeto(Funcionario,dados.get('atendente'))
    if not exerce(atendente,'ATENDENTE',agora): raise ValidationError('Funcionário não exerce o cargo de atendente agora.')
    cliente=objeto(Cliente,dados['cliente']) if dados.get('cliente') else None
    mesa=objeto(Mesa,dados['mesa']) if dados.get('mesa') else None
    pedido=salvar(Pedido(cliente=cliente,atendente=atendente,mesa=mesa,canal=dados.get('canal'),modalidade=dados.get('modalidade')))
    if pedido.canal=='APP' and pedido.modalidade=='LOCAL': raise ValidationError('Aplicativo aceita retirada ou delivery.')
    for linha in itens:
        produto=objeto(Produto,linha.get('produto'))
        if not produto.ativo: raise ValidationError('Produto indisponível.')
        consumo=composicao(produto)
        valor,promocao=preco(produto,agora)
        item=salvar(ItemPedido(pedido=pedido,produto=produto,quantidade=inteiro(linha.get('quantidade')),preco_base=valor,promocao=promocao,observacao=linha.get('observacao','')))
        grupos=set();vistos=set()
        for pk in linha.get('variacoes',[]):
            v=objeto(Variacao,pk)
            if v.produto_id!=produto.id or v.grupo in grupos: raise ValidationError('Variação incompatível ou repetida no mesmo grupo.')
            grupos.add(v.grupo)
            salvar(ItemVariacao(item=item,variacao=v,acrescimo=v.acrescimo))
        for extra in linha.get('adicionais',[]):
            a=objeto(Adicional,extra.get('adicional'))
            if a.id in vistos or not ProdutoAdicional.objects.filter(produto=produto,adicional=a).exists(): raise ValidationError('Adicional repetido ou incompatível.')
            vistos.add(a.id);qtd=inteiro(extra.get('quantidade',1))
            salvar(ItemAdicional(item=item,adicional=a,preco=a.preco,quantidade=qtd))
            for r in a.receita.all(): consumo[r.ingrediente_id]+=r.quantidade*qtd
        for insumo,qtd in consumo.items(): salvar(ConsumoItem(item=item,ingrediente_id=insumo,quantidade=qtd*item.quantidade))
    if pedido.modalidade=='DELIVERY':
        e=dados.get('entrega') or {}
        entregador=objeto(Funcionario,e.get('entregador'))
        if not exerce(entregador,'ENTREGADOR',agora): raise ValidationError('Entregador não exerce essa função agora.')
        distancia=moeda(e.get('distancia_km'))
        taxa=moeda(D('5')+distancia*D('1.5'))
        salvar(Entrega(pedido=pedido,entregador=entregador,distancia_km=distancia,taxa=taxa,**{k:e.get(k,'') for k in ['logradouro','numero','complemento','bairro','cidade','cep']}))
    elif dados.get('entrega'): raise ValidationError('Somente delivery pode conter entrega.')
    if dados.get('cupom'):
        if not cliente: raise ValidationError('Cupom exige cliente identificado.')
        # Serializa resgates do mesmo cupom; UNIQUE é a segunda proteção.
        cupom=Cupom.objects.select_for_update().filter(codigo=dados['cupom']).first()
        if not cupom or not cupom.inicio<=agora<cupom.fim: raise ValidationError('Cupom inexistente ou fora da validade.')
        if UsoCupom.objects.filter(cupom=cupom,cliente=cliente).exists(): raise ValidationError('Cliente já utilizou este cupom.')
        subtotal=pedido.subtotal
        pedido.desconto=min(subtotal,moeda(cupom.valor if cupom.tipo=='VALOR' else subtotal*cupom.valor/100))
        salvar(pedido);salvar(UsoCupom(pedido=pedido,cupom=cupom,cliente=cliente))
    pagamentos=dados.get('pagamentos',[])
    if not isinstance(pagamentos,list): raise ValidationError('Lista de pagamentos inválida.')
    total_pago=D('0');formas=set()
    for p in pagamentos:
        forma=objeto(FormaPagamento,p.get('forma'))
        if forma.id in formas: raise ValidationError('Some os valores da mesma forma de pagamento.')
        formas.add(forma.id);valor=moeda(p.get('valor'))
        salvar(Pagamento(pedido=pedido,forma=forma,valor=valor));total_pago+=valor
    if total_pago!=pedido.total: raise ValidationError(f'Pagamentos somam R$ {total_pago}; total correto: R$ {pedido.total:.2f}.')
    salvar(HistoricoStatus(pedido=pedido,status='RECEBIDO'))
    return pedido

TRANSICOES={'RECEBIDO':['EM_PREPARO','CANCELADO'],'EM_PREPARO':['PRONTO','CANCELADO'],'PRONTO':['SAIU_ENTREGA','CONCLUIDO','CANCELADO'],'SAIU_ENTREGA':['CONCLUIDO','CANCELADO'],'CONCLUIDO':[],'CANCELADO':[]}

def proximos(pedido):
    return [x for x in TRANSICOES[pedido.status] if not (x=='SAIU_ENTREGA' and pedido.modalidade!='DELIVERY') and not(x=='CONCLUIDO' and pedido.modalidade=='DELIVERY' and pedido.status=='PRONTO')]

@transaction.atomic
def mudar_status(pk,status):
    pedido=Pedido.objects.select_for_update().get(pk=pk)
    if status not in proximos(pedido): raise ValidationError('Transição de status inválida.')
    salvar(HistoricoStatus(pedido=pedido,status=status));return pedido

@transaction.atomic
def avaliar(pk,dados):
    pedido=Pedido.objects.select_for_update().get(pk=pk)
    if pedido.status!='CONCLUIDO' or not pedido.cliente_id: raise ValidationError('Avaliação exige pedido concluído e cliente identificado.')
    if Avaliacao.objects.filter(pedido=pedido).exists(): raise ValidationError('Pedido já avaliado.')
    return salvar(Avaliacao(pedido=pedido,nota=dados.get('nota'),comentario=dados.get('comentario','')))
