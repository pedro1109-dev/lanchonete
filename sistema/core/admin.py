from django.contrib import admin
from django.apps import apps
from . import models as m

admin.site.site_header='Sabor & Cia · Cadastros'
admin.site.site_title='Sabor & Cia'
admin.site.index_title='Cadastros e composição do cardápio'

class ReceitaInline(admin.TabularInline):
    model=m.Receita;extra=1
class ComponenteInline(admin.TabularInline):
    model=m.ComponenteCombo;fk_name='combo';extra=2
class VariacaoInline(admin.TabularInline):
    model=m.Variacao;extra=0
class AdicionalInline(admin.TabularInline):
    model=m.ProdutoAdicional;extra=0
@admin.register(m.Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display=['nome','categoria','preco_base','combo','ativo']
    list_filter=['categoria','combo','ativo'];search_fields=['nome']
    inlines=[ReceitaInline,ComponenteInline,VariacaoInline,AdicionalInline]

class ExercicioInline(admin.TabularInline):
    model=m.ExercicioCargo;extra=1
@admin.register(m.Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display=['nome','contato','ativo'];search_fields=['nome'];inlines=[ExercicioInline]

# Dados transacionais são imutáveis no admin. Escrita passa pelo serviço de pedidos.
class SomenteLeitura(admin.ModelAdmin):
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False

historicos={m.Pedido,m.ItemPedido,m.ItemVariacao,m.ItemAdicional,m.Pagamento,m.HistoricoStatus,m.UsoCupom,m.Entrega,m.Avaliacao,m.ConsumoItem}
for model in apps.get_app_config('core').get_models():
    if model in [m.Produto,m.Funcionario]: continue
    if model in historicos: admin.site.register(model,SomenteLeitura)
    else:
        attrs={'list_display':[f.name for f in model._meta.fields]}
        if any(f.name=='nome' for f in model._meta.fields):attrs['search_fields']=['nome']
        admin.site.register(model,type(model.__name__+'Admin',(admin.ModelAdmin,),attrs))
