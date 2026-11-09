# Sabor & Cia — sistema de lanchonete

Projeto fullstack com Python/Django, PostgreSQL, HTML, CSS e JavaScript. Inclui modelagem, 29 models de domínio, migrations, cadastros, atendimento, relatórios, Docker e evidências de testes.

## Comece aqui

1. Extraia o ZIP inteiro e abra a pasta `sabor_cia` no VS Code (Arquivo → Abrir Pasta).
2. Para experimentar no Windows, com Python 3.12 ou 3.13 instalado, execute `iniciar_windows.bat`. Ele cria `.venv`, instala dependências, cria um banco SQLite de demonstração e inicia o sistema.
3. Para a entrega com PostgreSQL e containers, use as instruções Docker abaixo.
4. Leia `documentacao/MER_justificativas.pdf` para compreender as decisões e hipóteses do projeto.

Não há `.venv` pré-compactada: ambientes virtuais dependem do caminho e do sistema operacional e devem ser criados na máquina de destino. Não incluí senhas fixas nem o banco usado nas capturas.

## Execução oficial: Docker Compose + PostgreSQL

Pré-requisitos: Docker Engine/Docker Desktop com Compose v2 e Python para gerar a configuração. Se não tiver Python no servidor, copie `.env.example` para `.env` e preencha as três chaves/senhas manualmente.

Na raiz, onde está `docker-compose.yml`:

```bash
python configurar.py
docker compose config
docker compose up --build -d
docker compose ps
docker compose logs --tail=100 backend
```

Abra **http://localhost:8080**. A inicialização aplica as migrations, coleta arquivos estáticos e cria os cadastros fictícios. Aguarde os serviços ficarem saudáveis.

**Credenciais de teste:** usuário `admin`; a senha é gerada e exibida por `configurar.py`, e fica em `ADMIN_PASSWORD` no `.env`. O comando não sobrescreve configuração existente. `seed_demo` não redefine senhas de usuários existentes. Para redefinir: `docker compose exec backend python manage.py changepassword admin`.

Três serviços:

- `frontend`: Nginx, porta 8080; fornece CSS/JS e encaminha HTML/API ao Django.
- `backend`: Django/Gunicorn, porta interna 8000 e porta local 127.0.0.1:8000 para diagnóstico.
- `db`: PostgreSQL 16, acessível pelo nome `db` na rede Docker; sem porta pública. Volume `dados_postgres` preserva os dados.

O volume `arquivos_estaticos` compartilha o resultado do collectstatic com o frontend. A conexão usa variáveis de ambiente. Não há credenciais no código-fonte.

Para encerrar preservando os dados: `docker compose down`. **Não use `down -v` para desligar normalmente: isso remove os volumes.**

## Rede da sala e aceite do deploy

Descubra o IP do servidor com `ipconfig` (Windows) ou `ip addr` (Linux). Exemplo para um servidor cujo IP seja `192.168.1.50`, mantendo localhost para o healthcheck:

```dotenv
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50
CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://192.168.1.50:8080
WEB_PORT=8080
```

Use o IP e a porta reais definidos pelo professor. Depois execute `docker compose up -d --force-recreate` e acesse `http://IP_DO_SERVIDOR:8080` em outra máquina da mesma rede. A porta precisa estar liberada no firewall da sala. A configuração é para demonstração em rede local, não uma publicação pública com HTTPS.

**Validação pendente no destino:** não houve acesso ao servidor da sala. Docker/PostgreSQL não foram executados neste ambiente; a tentativa de preparar PostgreSQL encontrou restrições de instalação. Foram verificados o YAML, o DDL gerado para PostgreSQL, as migrations, a aplicação com SQLite e o fluxo real no navegador. Não considere esses testes prova de deploy no servidor. Execute o roteiro de aceite em `evidencias/VALIDACAO.md`.

## Execução local no Windows sem Docker

Execute `iniciar_windows.bat`, ou no PowerShell:

```powershell
python configurar.py
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r sistema/requirements.txt
$env:USE_SQLITE="1"
$env:DEBUG="1"
.\.venv\Scripts\python.exe sistema/manage.py migrate
.\.venv\Scripts\python.exe sistema/manage.py seed_demo
.\.venv\Scripts\python.exe sistema/manage.py runserver
```

Abra **http://127.0.0.1:8000**. SQLite serve somente para demonstração rápida e testes; para a entrega utilize PostgreSQL. Gunicorn é instalado somente em sistemas diferentes de Windows; localmente o Django usa `runserver`.

No VS Code: Ctrl+Shift+P → Python: Select Interpreter → `.venv/Scripts/python.exe`.

Linux/macOS: `sh instalar_local.sh`. O ambiente virtual exige suporte `venv` na instalação do Python. Instalação inicial exige internet para baixar os pacotes.

Para PostgreSQL já instalado, configure `DB_HOST`, `DB_PORT`, `POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD` no `.env`, use `USE_SQLITE=0`, crie previamente o banco/usuário e execute migrate. Para desenvolvimento local com estáticos, use `DEBUG=1`. O fluxo recomendado para entrega é Docker.

## Uso do sistema

1. Entre com a conta gerada. Em **Cadastros e cardápio**, gerencie clientes, fornecedores, ingredientes, equipe e cardápio.
2. Cada funcionário precisa de um período em **ExercicioCargo**. Ana exerce ATENDENTE e GERENTE; Leo exerce ENTREGADOR na demonstração.
3. Produtos simples precisam de receita; combos precisam de dois produtos distintos na composição. No formulário do produto há seções para receita, componentes, variações e adicionais permitidos. Adicionais e suas receitas também têm cadastro próprio.
4. Em **Novo pedido**, selecione atendimento, cliente quando necessário, atendente e itens. Escolha variações, adicionais e observações. Delivery exige endereço, distância e entregador. Consumo local exige mesa.
5. Informe as formas de pagamento. Use **Preencher saldo na primeira forma** e, se desejar, divida o valor em outra forma. O backend recalcula todos os valores; o total do frontend é uma prévia.
6. Registre e acompanhe em **Acompanhar pedidos**. Cada ação registra data/hora. O histórico fica disponível no cartão do pedido.
7. Em **Relatórios**, filtre datas/cliente e veja vendas, histórico e consumo de ingredientes. Datas usam America/Sao_Paulo.
8. Avaliações podem ser registradas pela equipe após conclusão de pedido com cliente identificado.

Demonstração: Burger R$25, Suco R$8, Combo R$30, Bacon extra R$4. Cupom `BEMVINDO10` concede 10% uma vez por cliente; validade de um ano a partir da instalação. Batata possui promoção de R$10 por sete dias. Os períodos ficam visíveis no cadastro.

## Organização dos arquivos

| Caminho | Conteúdo |
|---|---|
| `documentacao/MER_justificativas.pdf` | Entidades, cardinalidades, atributos, regras, 3FN e justificativas |
| `documentacao/DER_completo.pdf` / `.svg` | Diagrama vetorial, com todos os atributos e relações; use zoom |
| `documentacao/DER_editavel.mmd` / `.dot` | Fontes editáveis do diagrama |
| `documentacao/dicionario_dados.pdf` / `.json` | Todos os campos, tipos, chaves, significados e restrições |
| `documentacao/modelo_logico.sql` | DDL PostgreSQL das 29 tabelas de domínio |
| `documentacao/REQUISITOS.md` | Matriz do enunciado e localização da implementação |
| `sistema/core/models.py` | Models e restrições do banco |
| `sistema/core/services.py` | Regras de venda, preços, cupom, entrega, status e avaliação |
| `sistema/core/views.py` | API e relatórios |
| `sistema/core/admin.py` | CRUD administrativo e proteção dos dados históricos |
| `sistema/core/migrations/` | Migração versionada do esquema |
| `sistema/templates/` e `sistema/static/` | HTML, CSS e JavaScript próprios |
| `sistema/tests/` | Testes de regras, API, CRUD e integridade |
| `sistema/core/management/commands/seed_demo.py` | Inicialização de dados fictícios |
| `docker-compose.yml`, `sistema/Dockerfile` | Infraestrutura de execução |
| `configurar.py`, `instalar_local.*`, `iniciar_windows.bat` | Preparação de ambiente |
| `evidencias/` | Capturas reais, resultado dos testes e roteiro do servidor |

## Banco: migrations versus SQL

O DDL é o modelo lógico para estudo e para criação isolada de um schema de domínio em banco vazio. **Para executar a aplicação, use `manage.py migrate`; não rode o DDL antes das migrations no mesmo banco.** Migrations também criam as tabelas internas de autenticação, sessões e administração do Django. O DER/dicionário cobrem o domínio; essas tabelas do framework são infraestrutura.

Regras locais (preço não negativo, quantidade positiva, unicidade, FK) ficam no banco e/ou na validação das models. Regras entre linhas (soma dos pagamentos, composição mínima, cargos no período, transições) ficam no serviço transacional. `full_clean()` não é executado automaticamente por `Model.save()` no shell; use os serviços ou formulários administrativos.

## Testes

Com o ambiente local preparado:

```powershell
$env:USE_SQLITE="1"
.\.venv\Scripts\python.exe sistema/manage.py test tests
```

No Docker, para verificar também o PostgreSQL:

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py test tests
```

Os testes usam um banco de teste separado, gerenciado pelo Django. O usuário PostgreSQL criado pela imagem oficial tem permissão de criar esse banco. Não aponte esse procedimento para um ambiente de produção.

## Limites explícitos

- O módulo é uma aplicação interna da equipe, não um aplicativo público para clientes. A origem APP é registrada pelo atendente.
- Estoque é mantido manualmente; consumo é estimado e congelado na venda. Não há compras, entrada de estoque automatizada, pagamento online, mapas ou estorno bancário.
- Variações alteram preço; observações livres não recalculam receita automaticamente. Há até uma variação por grupo; opções são opcionais.
- Cancelamento não libera o cupom para reutilização. Relatórios excluem cancelados; preservam-se pagamentos históricos para auditoria.
- Totais são derivados; preços históricos não mudam com o cardápio. Consultas de histórico exibem até 100 pedidos; totais/agrupamentos do relatório abrangem todo o filtro.
- Os testes não simulam concorrência real de PostgreSQL. Locks e restrições foram implementados, mas o aceite em PostgreSQL/Compose deve ocorrer no servidor de destino.
- Confirmar com a turma a notação Pé-de-Galinha e a escolha de Django/PostgreSQL, conforme o enunciado.

## Fontes técnicas

- https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- https://docs.djangoproject.com/en/5.2/ref/models/constraints/
- https://docs.docker.com/compose/how-tos/startup-order/
