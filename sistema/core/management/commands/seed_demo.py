import os
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from core.models import *

class Command(BaseCommand):
    help='Cria dados fictícios e usuário de demonstração sem apagar dados existentes.'
    @transaction.atomic
    def handle(self,*args,**kwargs):
        senha=os.getenv('ADMIN_PASSWORD')
        if not senha:raise CommandError('Defina ADMIN_PASSWORD no .env.')
        User=get_user_model();nome=os.getenv('ADMIN_USER','admin')
        if not User.objects.filter(username=nome).exists():User.objects.create_superuser(nome,'admin@example.test',senha)
        if Produto.objects.exists():
            self.stdout.write('Cardápio já existe; nenhum dado de negócio foi alterado.');return
        agora=timezone.now()
        cargos={c:Cargo.objects.create(nome=c.title(),codigo=c) for c in ['ATENDENTE','COZINHEIRO','ENTREGADOR','GERENTE']}
        ana=Funcionario.objects.create(nome='Ana · Atendimento',contato='ana@example.test')
        leo=Funcionario.objects.create(nome='Leo · Entregas',contato='leo@example.test')
        for f,c in [(ana,'ATENDENTE'),(ana,'GERENTE'),(leo,'ENTREGADOR')]:ExercicioCargo.objects.create(funcionario=f,cargo=cargos[c],inicio=agora-timedelta(days=30))
        Cliente.objects.create(nome='Marina Silva (demonstração)',contato='marina@example.test')
        for n in range(1,6):Mesa.objects.create(numero=n)
        fornecedor=Fornecedor.objects.create(nome='Distribuidora Exemplo',contato='vendas@example.test')
        insumos={nome:Ingrediente.objects.create(nome=nome,unidade=un,estoque=100,fornecedor=fornecedor) for nome,un in [('Pão','un'),('Hambúrguer','kg'),('Queijo','kg'),('Suco','l'),('Batata','kg'),('Bacon','kg')]}
        categorias={n:Categoria.objects.create(nome=n) for n in ['Lanches','Bebidas','Porções','Sobremesas','Combos']}
        burger=Produto.objects.create(nome='Burger da casa',categoria=categorias['Lanches'],preco_base=25)
        suco=Produto.objects.create(nome='Suco natural',categoria=categorias['Bebidas'],preco_base=8)
        batata=Produto.objects.create(nome='Batata crocante',categoria=categorias['Porções'],preco_base=12)
        for produto,nome,qtd in [(burger,'Pão',1),(burger,'Hambúrguer','.150'),(burger,'Queijo','.030'),(suco,'Suco','.300'),(batata,'Batata','.200')]:Receita.objects.create(produto=produto,ingrediente=insumos[nome],quantidade=qtd)
        combo=Produto.objects.create(nome='Combo da casa',categoria=categorias['Combos'],preco_base=30,combo=True)
        ComponenteCombo.objects.create(combo=combo,produto=burger,quantidade=1);ComponenteCombo.objects.create(combo=combo,produto=suco,quantidade=1)
        Variacao.objects.create(produto=burger,nome='Ao ponto',grupo='Ponto',acrescimo=0)
        Variacao.objects.create(produto=burger,nome='Bem passado',grupo='Ponto',acrescimo=0)
        adicional=Adicional.objects.create(nome='Bacon extra',preco=4)
        ReceitaAdicional.objects.create(adicional=adicional,ingrediente=insumos['Bacon'],quantidade='.040')
        for p in [burger,combo]:ProdutoAdicional.objects.create(produto=p,adicional=adicional)
        for n in ['Pix','Dinheiro','Cartão']:FormaPagamento.objects.create(nome=n)
        Cupom.objects.create(codigo='BEMVINDO10',tipo='PERCENTUAL',valor=10,inicio=agora-timedelta(days=1),fim=agora+timedelta(days=365))
        promocao=Promocao.objects.create(nome='Semana da batata',inicio=agora-timedelta(days=1),fim=agora+timedelta(days=7))
        PromocaoProduto.objects.create(promocao=promocao,produto=batata,preco=10)
        self.stdout.write(self.style.SUCCESS('Dados fictícios criados. Login definido no .env.'))
