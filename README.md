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

# 5. Subir a API
uvicorn app.main:app --reload
```

> Após configurar o .env, execute python -m alembic upgrade head. As instruções do seed serão acrescentadas pelo Membro 3.

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
  controllers/         # rotas HTTP: recebem a requisição e devolvem a resposta
  usecases/            # regras de negócio (uma função por ação do sistema)
  repositories/        # acesso ao banco (consultas com SQLAlchemy)
  models/              # tabelas do banco (SQLAlchemy)
  schemas/             # modelos Pydantic de entrada e saída
  infrastructure/      # detalhes técnicos: config, banco, bcrypt e JWT
alembic/               # migrations
tests/                 # testes automatizados
```

## **Padrão de respostas e erros**

> TODO (Membro 5): documentar o formato de sucesso, paginação e erros (400, 404, 422).

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

A migration inicial foi escrita manualmente. Nesta entrega, a sintaxe Python foi conferida. A execução de Alembic e pytest ficou pendente porque a instalação das dependências não foi concluída no ambiente de verificação.


## **Seed (dados iniciais)**

> TODO (Membro 3): como rodar `python -m app.seed` e as credenciais do admin de desenvolvimento.

## **Fluxo de trabalho no Git**

- Uma branch por tarefa (`feat/db-migrations`, `feat/seed`, `feat/rooms-crud`, ...).
- Commits pequenos, com mensagem descritiva.
- Pull Request revisado por outro membro antes de ir para a `main`.