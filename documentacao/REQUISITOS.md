# Matriz de requisitos — enunciado → implementação

| Seção | Requisito | Implementação / evidência |
|---|---|---|
| 4.1 | Cliente opcional; obrigatório em APP/delivery; histórico | Cliente, Pedido; constraint `pedido_cliente_obrigatorio`; filtro dos relatórios |
| 4.1 | Consumo local ligado a mesa | Mesa, FK opcional e constraint `pedido_mesa_modalidade` |
| 4.2 | Categorias e preço-base | Categoria, Produto; CRUD no admin |
| 4.2 | Combo com 2+ produtos e preço próprio | Produto.combo, ComponenteCombo; validação na venda |
| 4.2 | Variações, adicionais e observações por item | Variacao, ProdutoAdicional, ItemVariacao, ItemAdicional, ItemPedido.observacao |
| 4.3 | Pedido com 1+ itens | ItemPedido; transação em criar_pedido |
| 4.3 | Divisão entre formas de pagamento | Pagamento, FormaPagamento; soma exata conferida no backend |
| 4.3 | Status e datas de transição | HistoricoStatus; fluxo e locks em mudar_status |
| 4.3 | Cupom, validade, valor/percentual, uma vez/cliente | Cupom, UsoCupom; lock e UNIQUE |
| 4.3 | Avaliação opcional | Avaliacao; nota 1..5, única após conclusão |
| 4.4 | Retirada/delivery; endereço e entregador | Pedido.modalidade, Entrega; validação de cargo |
| 4.4 | Taxa por distância | Entrega.distancia_km/taxa; regra assumida R$5 + R$1,50/km |
| 4.5 | Múltiplos cargos por período | Funcionario, Cargo, ExercicioCargo |
| 4.5 | Atendente por pedido | Pedido.atendente; necessário cargo ATENDENTE vigente |
| 4.6 | Receita N:N e quantidades | Receita; insumos para produtos simples |
| 4.6 | Estoque, unidade, fornecedor | Ingrediente, Fornecedor |
| 4.6 | Estimativa de consumo | ConsumoItem; snapshot de produto, combo e adicionais |
| 4.7 | Promoções sazonais N:N e histórico | Promocao, PromocaoProduto; FK da promoção aplicada no item |
| 5.1 | Frontend/backend/banco separados | Nginx, Django/Gunicorn, PostgreSQL no Compose |
| 5.2 | CRUD dos cadastros principais | Django Admin: clientes, produtos, ingredientes, fornecedores, equipe; exclusão protegida se houver referência |
| 5.2 | Pedido completo, status e consulta relacional | Interface própria + API; capturas 02, 03, 04 |
| 5.3 | HTML semântico, CSS próprio, JS/fetch e feedback | templates/index.html, static/app.css, static/app.js |
| 5.4 | Dockerfile, Compose raiz, rede, volume e .env | Arquivos incluídos; validação real no servidor pendente |
| 5.5 | DDL, inicialização, README e evidências | modelo_logico.sql, migrations, seed_demo, READMEs, evidencias/ |
| 7.1 | MER e três justificativas | MER_justificativas.pdf, com seis justificativas |
| 7.2 | DER gráfico | DER_completo.pdf/.svg; fontes .dot e .mmd |
| 7.3 | Dicionário completo | dicionario_dados.pdf e cópia estruturada .json |
| 7.4 | Modelo lógico e 3FN | modelo_logico.sql; seção 5 do MER |
| 7.5 / 9 | Sistema e deploy em sala | Código entregue; execução/demonstração no servidor da sala ainda necessária |

Os documentos apresentam decisões assumidas onde o enunciado não define uma política. A implementação não inclui um aplicativo público, processamento bancário ou baixa automática de estoque, que não são funcionalidades mínimas exigidas. A quantidade mínima de componentes/receitas é validada antes da venda; cadastros podem ser preparados em etapas.
