# API de Reserva de Salas

## **Stack**

FastAPI · SQLAlchemy 2 · Alembic · Pydantic · bcrypt · PyJWT · pytest (TestClient) · SQLite

## **Pré-requisitos**

- [Python](https://www.python.org/downloads/) 3.10 ou superior
- [Git](https://git-scm.com/downloads)

## **Como rodar**

```powershell
# 1. Clonar o repositório e entrar na pasta do projeto
git clone https://github.com/ArthurPeruchi/API-Reserva-de-Salas.git
cd API-Reserva-de-Salas

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Configurar as variáveis de ambiente
copy .env.example .env        # Linux/macOS: cp .env.example .env
# Depois edite o arquivo .env, preenchendo DATABASE_URL, ADMIN_EMAIL e ADMIN_PASSWORD

# 5. Aplicar as migrations e cadastrar os dados de desenvolvimento
python -m alembic upgrade head
python -m app.seed

# 6. Subir a API
uvicorn app.main:app --reload
```

Para confirmar que a API subiu, acesse http://127.0.0.1:8000/api/health: a resposta deve ser `{"status": "ok"}`.

Documentação interativa (Swagger): http://127.0.0.1:8000/docs

O banco de dados SQLite (`reservas.db`) é criado localmente na raiz do projeto, na pasta de onde a API é executada.

### **Problemas comuns no Windows**

- **`.venv\Scripts\activate` bloqueado por política de execução:** rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` no PowerShell e tente de novo.
- **`pytest.exe` bloqueado por política de controle de aplicativos:** use `python -m pytest` (veja a seção Testes).

## **Testes**

```powershell
python -m pytest
```

## **Arquitetura**

O projeto é organizado em camadas. O fluxo de uma requisição segue sempre no mesmo sentido:

`controller → usecase → repository → model`

```
app/
  main.py              # cria o app e registra controllers e handlers de erro
  seed.py              # popula o banco (admin e salas de exemplo)
  core/                # hash e verificação de senhas com bcrypt
  controllers/         # rotas HTTP: recebem a requisição e devolvem a resposta
  usecases/            # regras de negócio (uma função por ação do sistema)
  repositories/        # acesso ao banco (consultas com SQLAlchemy)
  models/              # tabelas do banco (SQLAlchemy)
  schemas/             # modelos Pydantic de entrada e saída
  infrastructure/      # detalhes técnicos: config e banco
alembic/               # migrations
tests/                 # testes automatizados
```

## **Padrão de respostas e erros**

### **Formato de sucesso:**

Padrão adotado para as rotas de CRUD:

| Operação | Status | Corpo |
| --- | --- | --- |
| Listar | 200 | Envelope paginado (veja Paginação) |
| Buscar por id | 200 | O recurso |
| Criar | 201 | O recurso criado |
| Atualizar (`PUT`) | 200 | O recurso atualizado, com todos os campos substituídos |
| Excluir | 204 | Sem corpo |

### **Formato de erro:**

Toda resposta de erro segue o mesmo corpo JSON:

```json
{
  "status": 404,
  "message": "Sala não encontrada."
}
```

Erros de validação (422) incluem também a lista `errors`, com o campo e o motivo de cada problema:

```json
{
  "status": 422,
  "message": "Dados inválidos.",
  "errors": [
    { "field": "name", "message": "Deve ter no mínimo 1 caractere(s)." },
    { "field": "capacity", "message": "Deve ser maior que 0." }
  ]
}
```

### **Códigos de status:**

| Código | Quando acontece |
| --- | --- |
| 400 | JSON malformado no corpo da requisição |
| 401 | Não autenticado ou token inválido (a partir da autenticação) |
| 403 | Autenticado, mas sem permissão para a ação (a partir da autenticação) |
| 404 | Recurso ou rota inexistente |
| 405 | Método HTTP não permitido na rota |
| 409 | Conflito com o estado atual dos dados, como excluir uma sala que possui reservas |
| 422 | Dados inválidos (campo ausente, tipo errado, valor fora do limite) |
| 500 | Erro interno; o detalhe fica no log e não é enviado ao cliente |

### **Paginação:**

As listagens aceitam os parâmetros de query abaixo:

| Parâmetro | Regra | Padrão |
| --- | --- | --- |
| `page` | inteiro, mínimo 1 | 1 |
| `size` | inteiro de 1 a 100 | 10 |

Exemplo: `GET /api/rooms?page=2&size=5`

A resposta traz os itens em `data` e o total de registros no banco em `total`:

```json
{
  "data": [],
  "page": 2,
  "size": 5,
  "total": 3
}
```

Uma página além da última devolve `data` vazio com status 200. Valores inválidos, como `page=0` ou `size=101`, devolvem 422.

## Banco de dados e migrations

O banco usa SQLAlchemy 2 e três tabelas.

| Tabela | Campos |
| --- | --- |
| users | id, name, email único, password_hash, role |
| rooms | id, name, capacity, location |
| reservations | id, room_id, user_id, start, end, reason |

Cada reserva pertence a um usuário e uma sala. User.reservations e Room.reservations permitem consultar as reservas relacionadas. O seed deve gravar o hash bcrypt em password_hash. O papel aceita user e admin, com user como padrão.

Depois de configurar o .env, aplique a migration antes de subir a API.

```powershell
python -m alembic upgrade head
python -m alembic current
```

A configuração usa get_settings().database_url e ativa PRAGMA foreign_keys=ON em cada conexão SQLite. Engines criados por create_database_engine também recebem essa configuração. Para bancos em memória, StaticPool compartilha a conexão entre as sessões e threads dos testes.

As chaves estrangeiras usam ON DELETE RESTRICT. A exclusão de sala ou usuário com reservas é bloqueada pelo banco. As relationships usam passive_deletes="all" para preservar esse comportamento mesmo com reservas carregadas na sessão.

Na integração do CRUD, o responsável pelo serviço de salas deve responder 409 com a mensagem "A sala possui reservas." quando a exclusão estiver bloqueada. Se o commit lançar IntegrityError, execute session.rollback() antes de reutilizar a sessão. O banco garante a integridade também quando uma reserva é criada durante a tentativa de exclusão.

Para conferir upgrade e downgrade em um banco novo, use um nome de arquivo que ainda não exista.

```powershell
$env:DATABASE_URL = "sqlite:///./verificacao_membro2.db"
python -m alembic upgrade head
python -m alembic check
python -m alembic downgrade base
python -m alembic upgrade head
Remove-Item Env:DATABASE_URL
```

downgrade base remove as tabelas e todos os seus dados. Os testes de tests/test_database.py usam um banco temporário para verificar o ciclo das migrations, e-mail único, chaves estrangeiras e bloqueio de exclusão com a coleção carregada e descarregada.

```powershell
python -m pytest
```

Para alterações futuras, gere uma migration e revise o conteúdo antes de aplicar.

```powershell
python -m alembic revision --autogenerate -m "descricao"
python -m alembic upgrade head
```

render_as_batch=True está configurado nos modos online e offline para alterações de tabelas SQLite.

A migration inicial foi escrita manualmente. Na validação do seed, o ciclo de migrations e a suíte de testes também foram executados com sucesso.


## **Seed (dados iniciais)**

Copie `.env.example` para `.env` e execute na raiz do projeto, após aplicar as migrations:

```powershell
python -m app.seed
```

Credenciais de desenvolvimento fornecidas no `.env.example` (use apenas localmente):

| Variável | Valor |
| --- | --- |
| ADMIN_EMAIL | admin@dominio.com |
| ADMIN_PASSWORD | AdminDev123! |

O seed lê `ADMIN_EMAIL`, `ADMIN_PASSWORD` e `DATABASE_URL` do `.env`; variáveis do ambiente têm precedência. As credenciais são obrigatórias. O administrador é criado com nome `Administrador` e papel `admin`. A senha é gravada somente como hash bcrypt em `users.password_hash`, usando `app/core/security.py`, sem passlib. Senhas novas devem ter de 1 a 72 bytes em UTF-8; senhas maiores são rejeitadas sem truncamento. Consulte a [documentação do bcrypt](https://github.com/pyca/bcrypt).

São cadastradas quatro salas: Sala 101 (30 lugares), Sala 102 (40), Laboratório de Informática (25) e Sala de Reuniões (10), cada uma com sua localização.

Antes de inserir, o seed consulta o usuário pelo e-mail e cada sala pelo nome. Registros existentes são preservados, incluindo senha, papel, capacidade e localização. Alterar a senha no `.env` não troca a senha de um usuário já cadastrado. Todas as inserções são realizadas em uma única transação.

Em um banco vazio, a primeira execução informa `1 administrador(es) e 4 sala(s) criados`. A segunda informa `0 administrador(es) e 0 sala(s) criados`. Se faltar uma sala, somente ela será inserida novamente.

```powershell
python -m pytest tests/test_security.py tests/test_seed.py
```

Os testes executam migrations e `python -m app.seed` duas vezes em um banco temporário, consultam o hash salvo e verificam a senha com bcrypt, além de conferir a ausência de duplicatas e a preservação de dados existentes. O `.env` e o banco local são ignorados pelo Git. Os testes adicionais do CRUD de salas ficam para quando suas rotas estiverem disponíveis.

## **Fluxo de trabalho no Git**

- Uma branch por tarefa (`feat/db-migrations`, `feat/seed`, `feat/rooms-crud`, ...).
- Commits pequenos, com mensagem descritiva.
- Pull Request revisado por outro membro antes de ir para a `main`.
