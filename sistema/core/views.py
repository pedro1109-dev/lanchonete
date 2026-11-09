import json
from functools import wraps
from datetime import date
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError, connection
from django.db.models import Sum, Q
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import *
from .services import criar_pedido,mudar_status,avaliar,preco,proximos


def api(fn):
    @wraps(fn)
    def wrapper(request,*args,**kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:return JsonResponse({'erro':'Faça login com uma conta da equipe.'},status=403)
        try:return fn(request,*args,**kwargs)
        except ValidationError as e:return JsonResponse({'erro':'; '.join(e.messages)},status=400)
        except ObjectDoesNotExist:return JsonResponse({'erro':'Registro não encontrado.'},status=404)
        except IntegrityError:return JsonResponse({'erro':'Registro duplicado ou conflito de integridade.'},status=409)
        except (ValueError,TypeError,KeyError,AttributeError):return JsonResponse({'erro':'Confira o formato e os campos enviados.'},status=400)
    return wrapper

def body(request):return json.loads(request.body or '{}')
def metodo():return JsonResponse({'erro':'Método não permitido.'},status=405)

@login_required
@ensure_csrf_cookie
def index(request):
    if not request.user.is_staff:return JsonResponse({'erro':'Acesso restrito à equipe.'},status=403)
    return render(request,'index.html')

def health(request):
    with connection.cursor() as c:c.execute('SELECT 1')
    return JsonResponse({'status':'ok'})

@api
def catalogo(request):
    if request.method!='GET':return metodo()
    agora=timezone.now();produtos=[]
    for p in Produto.objects.filter(ativo=True).select_related('categoria'):
        valor,promo=preco(p,agora)
        produtos.append({'id':p.id,'nome':p.nome,'categoria':p.categoria.nome,'combo':p.combo,'preco':valor,'variacoes':list(p.variacoes.values('id','nome','grupo','acrescimo')),'adicionais':[{'id':x.adicional.id,'nome':x.adicional.nome,'preco':x.adicional.preco} for x in p.adicionais_permitidos.select_related('adicional')]})
    return JsonResponse({'produtos':produtos,'clientes':list(Cliente.objects.values('id','nome')),'mesas':list(Mesa.objects.values('id','numero')),'funcionarios':list(Funcionario.objects.filter(ativo=True).values('id','nome')),'formas':list(FormaPagamento.objects.values('id','nome')),'cupons':list(Cupom.objects.filter(inicio__lte=agora,fim__gt=agora).values('codigo','tipo','valor')),'taxa_base':'5.00','taxa_km':'1.50'})

def serializar(p):
    return {'id':p.id,'cliente':p.cliente.nome if p.cliente else 'Balcão sem identificação','criado_em':p.criado_em.isoformat(),'modalidade':p.modalidade,'status':p.status,'proximos':proximos(p),'subtotal':p.subtotal,'desconto':p.desconto,'taxa':p.entrega.taxa if hasattr(p,'entrega') else 0,'total':p.total,'itens':[{'produto':i.produto.nome,'quantidade':i.quantidade,'total':i.total,'observacao':i.observacao,'variacoes':[v.variacao.nome for v in i.variacoes.all()],'adicionais':[f'{a.quantidade}x {a.adicional.nome}' for a in i.adicionais.all()]} for i in p.itens.all()],'pagamentos':[{'forma':v.forma.nome,'valor':v.valor} for v in p.pagamentos.all()],'historico':list(p.historico.values('status','ocorrido_em')),'avaliacao':p.avaliacao.nota if hasattr(p,'avaliacao') else None}

@api
def pedidos(request):
    if request.method=='POST':return JsonResponse(serializar(criar_pedido(body(request))),status=201)
    if request.method!='GET':return metodo()
    qs=Pedido.objects.all()
    if request.GET.get('cliente'):qs=qs.filter(cliente_id=request.GET['cliente'])
    return JsonResponse({'pedidos':[serializar(p) for p in qs[:100]]})

@api
def status(request,pk):
    if request.method!='POST':return metodo()
    return JsonResponse(serializar(mudar_status(pk,body(request).get('status'))))

@api
def avaliacao(request,pk):
    if request.method!='POST':return metodo()
    a=avaliar(pk,body(request));return JsonResponse({'nota':a.nota},status=201)

@api
def relatorio(request):
    if request.method!='GET':return metodo()
    qs=Pedido.objects.exclude(historico__status='CANCELADO')
    for campo,lookup in [('inicio','criado_em__date__gte'),('fim','criado_em__date__lte')]:
        if request.GET.get(campo):qs=qs.filter(**{lookup:date.fromisoformat(request.GET[campo])})
    if request.GET.get('cliente'):qs=qs.filter(cliente_id=request.GET['cliente'])
    vendas=ItemPedido.objects.filter(pedido__in=qs).values('produto__nome').annotate(quantidade=Sum('quantidade')).order_by('-quantidade')
    consumo=ConsumoItem.objects.filter(item__pedido__in=qs).values('ingrediente__nome','ingrediente__unidade').annotate(quantidade=Sum('quantidade')).order_by('ingrediente__nome')
    return JsonResponse({'quantidade_pedidos':qs.count(),'valor_vendas':sum((p.total for p in qs),Decimal(0)),'vendas':list(vendas),'consumo':list(consumo),'pedidos':[serializar(p) for p in qs[:100]]})
