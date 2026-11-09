# Código-fonte

O guia completo está em `../README.md`. Abra a pasta superior `sabor_cia` no VS Code.

- Models: `core/models.py` (29 tabelas de domínio).
- Regras transacionais: `core/services.py`.
- API: `core/views.py`; rotas em `config/urls.py`.
- CRUD: Django Admin em `/admin/`, com autenticação.
- Interface: `templates/index.html`, `static/app.css`, `static/app.js`.
- Dados de exemplo: `python manage.py seed_demo` após configurar ambiente e migrar.
- O Docker Compose é executado na raiz superior, onde ficam `.env` e `docker-compose.yml`.
- Dependências: Python 3.12/3.13 e `requirements.txt`. A versão de Python testada foi 3.12.

API autenticada (sessão + CSRF nas escritas):

| Método | Rota | Função |
|---|---|---|
| GET | `/api/catalogo/` | Cardápio, opções, clientes e formas de pagamento |
| GET | `/api/pedidos/?cliente=ID` | Últimos 100 pedidos, com filtro opcional |
| POST | `/api/pedidos/` | Criação transacional do pedido completo |
| POST | `/api/pedidos/ID/status/` | `{"status":"EM_PREPARO"}` |
| POST | `/api/pedidos/ID/avaliacao/` | `{"nota":5,"comentario":"Muito bom"}` |
| GET | `/api/relatorio/?inicio=2026-11-01&fim=2026-11-30&cliente=ID` | Agregados e histórico |
| GET | `/health/` | Verifica comunicação com banco |

O CRUD administrativo usa formulários Django e respostas HTML. Atendimento e relatórios usam fetch/JSON. IDs do seed devem ser consultados no catálogo; não dependa de números fixos.

Exemplo do corpo de pedido, substituindo os IDs pelos existentes:

```json
{
  "canal": "BALCAO",
  "modalidade": "RETIRADA",
  "atendente": 1,
  "cliente": null,
  "mesa": null,
  "itens": [{"produto": 1, "quantidade": 1, "variacoes": [], "adicionais": [], "observacao": "sem cebola"}],
  "pagamentos": [{"forma": 1, "valor": "25.00"}]
}
```

O preço enviado pelo navegador não é aceito: os valores são calculados pelo serviço. Erros de validação retornam JSON com `erro` e status 400; conflito retorna 409, ausência de autenticação 403. Cadastro e histórico possuem proteção de referências por FK.
