# Validação realizada e aceite do servidor

## Executado neste ambiente

- Python 3.12, Django 5.2.19, SQLite: 20 testes passaram (`testes_sqlite.txt`).
- `manage.py check`: nenhum problema.
- `makemigrations --check --dry-run`: nenhuma alteração pendente.
- Chromium headless: login, cadastro, pedido com combo/adicional/cupom, pagamento, mudança de status, relatório relacional e layout de 390 px passaram (`teste_interface.txt`).
- Capturas são da aplicação em execução com dados fictícios, não mockups.
- DDL PostgreSQL gerado usando o schema editor do backend PostgreSQL, sem conectar a servidor.
- YAML do Compose analisado estruturalmente; não equivale a `docker compose up`.

## Evidências incluídas

1. `01_cadastro_cliente.png`: cliente cadastrado e listado no painel.
2. `02_pedido_preenchido.png`: combo + bacon, observação, cupom e pagamento de R$30,60.
3. `03_pedido_registrado.png`: persistência confirmada e evento RECEBIDO.
4. `04_relatorio_relacionamentos.png`: pedido, produtos e ingredientes estimados relacionados.
5. `05_mobile.png`: interface em viewport de 390 px.

## Pendente: executar no servidor da sala

Docker e PostgreSQL não foram executados aqui. Não há comprovação de implantação no servidor da sala nem teste de concorrência real no PostgreSQL.

1. Configurar `.env`, IP/porta da LAN e executar `docker compose config`.
2. Executar `docker compose up --build -d`; conferir saúde com `docker compose ps` e logs.
3. Abrir a URL de outra máquina da sala e realizar login.
4. Executar `docker compose exec backend python manage.py test tests` para rodar os mesmos testes no PostgreSQL.
5. Cadastrar um cliente, editar e excluir um cadastro sem dependências.
6. Registrar um pedido com dois pagamentos, conferir total, atualizar status e abrir o histórico.
7. Registrar delivery com endereço/entregador, conferir taxa e fluxo de saída.
8. Conferir consumo estimado, filtro de cliente e exclusão de cancelados no relatório.
9. Reiniciar com `docker compose restart` e confirmar que os dados persistem.
10. Capturar novas imagens com a URL/IP real e anexar à apresentação. Registrar data, servidor e responsável pela validação.

Critério: frontend acessível na LAN, backend consultando PostgreSQL, cadastros e pedidos persistidos após reinício.
