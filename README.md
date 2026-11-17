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

> As etapas de migrations e de seed serão acrescentadas aqui pelos Membros 2 e 3, entre as etapas 4 e 5.

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

## **Banco de dados e migrations**

> TODO (Membro 2): como aplicar as migrations (`alembic upgrade head`) e diagrama das tabelas.

## **Seed (dados iniciais)**

> TODO (Membro 3): como rodar `python -m app.seed` e as credenciais do admin de desenvolvimento.

## **Fluxo de trabalho no Git**

- Uma branch por tarefa (`feat/db-migrations`, `feat/seed`, `feat/rooms-crud`, ...).
- Commits pequenos, com mensagem descritiva.
- Pull Request revisado por outro membro antes de ir para a `main`.