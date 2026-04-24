# 🦸 Superhero API

Backend em **Python/FastAPI** para gerenciamento de super-heróis com banco de dados **PostgreSQL**, integração com a **SuperheroAPI** externa, **chat com IA via Groq** e **servidor MCP** para integração com clientes de IA como o Claude Desktop.

---

## 📚 Sumário

- [Visão Geral](#-visão-geral)
- [Tecnologias](#-tecnologias)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Banco de Dados](#-banco-de-dados)
- [Executando a API](#-executando-a-api)
- [Endpoints](#-endpoints)
- [Chat com IA Groq](#-chat-com-ia-groq)
- [MCP Server](#-mcp-server)
- [Exemplos de Uso](#-exemplos-de-uso)
- [Resolução de Problemas](#-resolução-de-problemas)
- [Licença](#-licença)

---

## 🔍 Visão Geral

A **Superhero API** é um backend completo que permite:

- Cadastrar, consultar, atualizar e deletar super-heróis via **CRUD REST**
- Importar heróis automaticamente da **SuperheroAPI** externa
- Conversar com uma **IA (Groq + LLaMA)** que consulta o banco em tempo real para responder perguntas sobre os heróis
- Expor todas as operações via **MCP Server**, permitindo que qualquer cliente MCP (como o Claude Desktop) acesse e interrogue o banco de dados diretamente

### 🧩 Modelo de dados

Os dados de cada herói são normalizados em **9 tabelas relacionais**:

- `superheroes` → dados principais (nome, imagem)
- `superhero_powerstats` → atributos de poder (0–100)
- `superhero_biography` → biografia completa
- `superhero_aliases` → apelidos (1:N)
- `superhero_appearance` → características físicas
- `superhero_heights` → alturas em múltiplas unidades (1:N)
- `superhero_weights` → pesos em múltiplas unidades (1:N)
- `superhero_work` → ocupação e base de operações
- `superhero_connections` → times e familiares

---

## 🛠 Tecnologias

| Tecnologia        | Versão    | Uso                               |
|-------------------|-----------|------------------------------------|
| Python            | 3.11+     | Linguagem principal               |
| FastAPI           | 0.115+    | Framework web                     |
| SQLAlchemy        | 2.0+      | ORM e acesso ao banco             |
| PostgreSQL        | 14+       | Banco de dados                    |
| Pydantic          | 2.x       | Validação e DTOs                  |
| httpx             | 0.27.x    | Chamadas HTTP externas            |
| OpenAI SDK        | 1.54+     | Integração com Groq               |
| Groq API          | —         | LLM gratuito com tool calling     |
| MCP SDK           | 1.2+      | Servidor Model Context Protocol   |
| Uvicorn           | 0.32+     | Servidor ASGI                     |

---

## 🧱 Estrutura do Projeto

```bash
superhero-api/
├── app/
│   ├── __init__.py
│   ├── main.py                         # entrypoint FastAPI
│   ├── config.py                       # variáveis de ambiente
│   ├── database.py                     # engine e sessão SQLAlchemy
│   ├── models.py                       # models / tabelas SQLAlchemy
│   ├── schemas.py                      # DTOs Pydantic
│   ├── crud.py                         # operações no banco
│   ├── routers/
│   │   ├── heroes.py                   # endpoints CRUD
│   │   ├── import_heroes.py            # importação da API externa
│   │   └── chat.py                     # endpoint de chat com IA
│   └── services/
│       ├── superhero_api_service.py    # integração SuperheroAPI
│       └── grok_service.py             # integração Groq + tools
├── mcp_server.py                       # servidor MCP standalone
├── .env                                # variáveis de ambiente (não versionar)
├── .env.example                        # template de variáveis
├── requirements.txt
└── README.md
```

---

## 📦 Pré-requisitos

- **Python 3.11** ou superior
- **PostgreSQL 14** ou superior (local ou em cloud)
- Conta gratuita no **Groq Console** para obter a API key

---

## 🧪 Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/superhero-api.git
cd superhero-api

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

`requirements.txt` (principais libs):

```text
fastapi>=0.115.6
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.36
psycopg2-binary>=2.9.10
python-dotenv>=1.0.1
openai>=1.54.0
mcp>=1.2.0
pydantic-settings>=2.6.1
httpx>=0.27.0,<0.28.0
starlette>=0.41.0
```

---

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/superhero_db
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama3-groq-70b-8192-tool-use-preview
```

### 🔑 Variáveis de Ambiente

| Variável       | Obrigatório | Padrão                                   | Descrição                         |
|----------------|-------------|------------------------------------------|-----------------------------------|
| `DATABASE_URL` | Sim         | —                                        | URL de conexão PostgreSQL         |
| `GROQ_API_KEY` | Sim         | —                                        | Chave da API Groq                 |
| `GROQ_MODEL`   | Não         | `llama3-groq-70b-8192-tool-use-preview` | Modelo LLM utilizado pelo Groq    |

### 🧠 Modelos Groq recomendados

| Modelo                              | Observação                                  |
|-------------------------------------|---------------------------------------------|
| `llama3-groq-70b-8192-tool-use-preview` | Recomendado — treinado para tool calling |
| `llama-3.3-70b-versatile`          | Boa performance geral                      |
| `mixtral-8x7b-32768`               | Contexto maior, bom para respostas longas  |

---

## 🗃 Banco de Dados

O banco é criado automaticamente ao iniciar a API via `Base.metadata.create_all()`.

Se preferir criar manualmente, DDL principal:

```sql
CREATE TABLE IF NOT EXISTS superheroes (
    id          SERIAL PRIMARY KEY,
    external_id VARCHAR(20)  UNIQUE NOT NULL,
    name        VARCHAR(150) NOT NULL,
    image_url   VARCHAR(500),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS superhero_powerstats (
    id           SERIAL PRIMARY KEY,
    superhero_id INTEGER NOT NULL REFERENCES superheroes(id) ON DELETE CASCADE,
    intelligence INTEGER, strength INTEGER, speed INTEGER,
    durability   INTEGER, power    INTEGER, combat INTEGER,
    UNIQUE (superhero_id)
);

CREATE TABLE IF NOT EXISTS superhero_biography (
    id               SERIAL PRIMARY KEY,
    superhero_id     INTEGER NOT NULL REFERENCES superheroes(id) ON DELETE CASCADE,
    full_name        VARCHAR(200),
    alter_egos       TEXT,
    place_of_birth   VARCHAR(300),
    first_appearance VARCHAR(200),
    publisher        VARCHAR(150),
    alignment        VARCHAR(50),
    UNIQUE (superhero_id)
);

CREATE TABLE IF NOT EXISTS superhero_aliases (
    id           SERIAL PRIMARY KEY,
    biography_id INTEGER NOT NULL REFERENCES superhero_biography(id) ON DELETE CASCADE,
    alias        VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS superhero_appearance (
    id           SERIAL PRIMARY KEY,
    superhero_id INTEGER NOT NULL REFERENCES superheroes(id) ON DELETE CASCADE,
    gender       VARCHAR(50),
    race         VARCHAR(100),
    eye_color    VARCHAR(50),
    hair_color   VARCHAR(50),
    UNIQUE (superhero_id)
);

CREATE TABLE IF NOT EXISTS superhero_heights (
    id            SERIAL PRIMARY KEY,
    appearance_id INTEGER NOT NULL REFERENCES superhero_appearance(id) ON DELETE CASCADE,
    value         VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS superhero_weights (
    id            SERIAL PRIMARY KEY,
    appearance_id INTEGER NOT NULL REFERENCES superhero_appearance(id) ON DELETE CASCADE,
    value         VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS superhero_work (
    id           SERIAL PRIMARY KEY,
    superhero_id INTEGER NOT NULL REFERENCES superheroes(id) ON DELETE CASCADE,
    occupation   VARCHAR(300),
    base         TEXT,
    UNIQUE (superhero_id)
);

CREATE TABLE IF NOT EXISTS superhero_connections (
    id                SERIAL PRIMARY KEY,
    superhero_id      INTEGER NOT NULL REFERENCES superheroes(id) ON DELETE CASCADE,
    group_affiliation TEXT,
    relatives         TEXT,
    UNIQUE (superhero_id)
);

CREATE INDEX IF NOT EXISTS idx_superheroes_name        ON superheroes(name);
CREATE INDEX IF NOT EXISTS idx_superheroes_external_id ON superheroes(external_id);
CREATE INDEX IF NOT EXISTS idx_biography_publisher     ON superhero_biography(publisher);
CREATE INDEX IF NOT EXISTS idx_biography_alignment     ON superhero_biography(alignment);
```

---

## ▶️ Executando a API

```bash
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🌐 Endpoints

### ✅ Health

| Método | Rota    | Descrição       |
|--------|---------|-----------------|
| GET    | `/`     | Status da API   |
| GET    | `/health` | Health check |

### 🦸 CRUD — Heroes

| Método | Rota                                   | Descrição                          |
|--------|----------------------------------------|------------------------------------|
| POST   | `/heroes/`                             | Cria um herói manualmente         |
| GET    | `/heroes/`                             | Lista todos os heróis (paginação) |
| GET    | `/heroes/{id}`                         | Busca herói por ID                |
| GET    | `/heroes/search?name=batman`          | Busca por nome parcial            |
| GET    | `/heroes/publisher/{publisher}`       | Filtra por editora                |
| GET    | `/heroes/alignment/{alignment}`       | Filtra por alinhamento            |
| PUT    | `/heroes/{id}`                        | Atualiza um herói                 |
| DELETE | `/heroes/{id}`                        | Remove um herói e dados ligados   |

### 🌎 Importação — SuperheroAPI Externa

| Método | Rota                            | Descrição                    |
|--------|---------------------------------|------------------------------|
| POST   | `/import/search/{query}`        | Busca e importa heróis      |
| GET    | `/import/heroes`               | Lista heróis importados     |
| GET    | `/import/heroes/search?name=bat` | Busca entre importados     |

Exemplos:

```http
POST /import/search/batman
POST /import/search/spider
POST /import/search/thor
POST /import/search/iron man
```

Heróis já existentes (mesmo `external_id`) são ignorados automaticamente.

### 💬 Chat com IA

| Método | Rota     | Descrição             |
|--------|----------|-----------------------|
| POST   | `/chat/` | Envia mensagem à IA  |

**Payload de entrada:**

```json
{
  "message": "Quais heróis da Marvel temos no banco?"
}
```

**Resposta:**

```json
{
  "response": "No banco de dados temos os seguintes heróis da Marvel Comics: ...",
  "tools_used": ["get_heroes_by_publisher"]
}
```

O campo `tools_used` mostra quais ferramentas a IA utilizou para montar a resposta.

---

## 🤖 Chat com IA Groq

O endpoint `/chat/` conecta a aplicação ao modelo LLaMA via **Groq** com **tool calling**.

A IA **não responde de memória**: ela decide quais ferramentas chamar, executa queries no banco em tempo real e formula a resposta com base nos dados reais.

### 🔄 Fluxo de uma requisição

1. Usuário envia mensagem
2. FastAPI recebe no `/chat/`
3. `GrokService` monta o histórico de mensagens
4. Envia para o modelo Groq com **26 tools** disponíveis
5. Modelo decide quais tools chamar
6. `GrokService` executa as queries no PostgreSQL
7. Resultado é devolvido ao modelo como contexto
8. Modelo formula a resposta final em linguagem natural
9. Resposta é retornada ao usuário com `tools_used`

### 🧰 Ferramentas disponíveis (26 tools)

**superheroes**

- `getallheroes`
- `getherobyid`
- `searchherobyname`
- `count_heroes`

**superhero_powerstats**

- `getpowerstatsbyhero`
- `gettopheroesbystat`
- `getallpowerstats`

**superhero_biography**

- `getbiographybyhero`
- `getheroesbypublisher`
- `getheroesbyalignment`
- `searchherobyrealname`
- `list_publishers`

**superhero_aliases**

- `getaliasesbyhero`
- `searchheroby_alias`

**superhero_appearance**

- `getappearancebyhero`
- `getheroesbyrace`
- `getheroesbygender`
- `list_races`

**superhero_heights / superhero_weights**

- `getheightandweightby_hero`

**superhero_work**

- `getworkbyhero`
- `searchheroesbybase`
- `searchheroesbyoccupation`

**superhero_connections**

- `getconnectionsbyhero`
- `searchheroesbygroup`
- `searchheroesbyrelative`

**Consultas cruzadas**

- `getfullheroprofile` (todas as tabelas de uma vez)
- `compareheroes_stats` (comparação lado a lado)

### 💡 Exemplos de perguntas para a IA

- "Quais heróis da Marvel estão cadastrados?"
- "Me conte tudo sobre o Batman"
- "Qual herói tem maior inteligência?"
- "Compare Spider-Man e Batman"
- "Quais vilões (alignment bad) temos no banco?"
- "Quem faz parte dos Avengers?"
- "Quais heróis são mutantes?"
- "Quantos heróis temos cadastrados no total?"
- "Quem tem Bruce Wayne como parente?"
- "Quais heróis operam em Gotham City?"
- "Me mostre o ranking dos 5 heróis mais rápidos"

---

## 🧩 MCP Server

O arquivo `mcp_server.py` implementa um servidor **Model Context Protocol (MCP)** standalone.

O MCP é um protocolo aberto (Anthropic) que permite que **clientes de IA** se conectem a fontes de dados externas de forma padronizada.

Com o MCP Server desta aplicação, você pode abrir o **Claude Desktop** e perguntar diretamente sobre os heróis no seu PostgreSQL local, sem precisar da API REST ou escrever código.

### 🔗 Arquitetura MCP

```text
Claude Desktop
      ↓  (MCP Protocol via stdio)
mcp_server.py
      ↓  (SQLAlchemy)
PostgreSQL — banco de super-heróis
```

### 🛠 Ferramentas expostas pelo MCP Server

| Ferramenta        | Descrição                       |
|-------------------|---------------------------------|
| `get_all_heroes`  | Lista todos os heróis          |
| `search_by_name`  | Busca por nome parcial         |
| `get_hero_by_id`  | Herói completo por ID          |
| `get_by_publisher`| Filtra por editora             |
| `get_by_alignment`| Filtra por alinhamento moral   |
| `count_heroes`    | Total de heróis cadastrados    |
| `import_hero`     | Importa da SuperheroAPI externa|

### ⚙️ Configurando com o Claude Desktop

**Passo 1.** Localize o arquivo de configuração:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Passo 2.** Adicione a configuração do servidor MCP.

**Windows:**

```json
{
  "mcpServers": {
    "superhero-db": {
      "command": "python",
      "args": ["C:\\caminho\\absoluto\\para\\superhero-api\\mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://usuario:senha@localhost:5432/superhero_db"
      }
    }
  }
}
```

**Linux / macOS:**

```json
{
  "mcpServers": {
    "superhero-db": {
      "command": "python",
      "args": ["/home/usuario/projetos/superhero-api/mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://usuario:senha@localhost:5432/superhero_db"
      }
    }
  }
}
```

**Passo 3.** Reinicie o Claude Desktop completamente.

**Passo 4.** Um ícone de ferramenta aparecerá indicando o servidor MCP conectado.

**Passo 5.** Exemplos de perguntas diretamente no Claude:

- "Quais heróis temos no banco de dados?"
- "Me mostre o perfil completo do Batman"
- "Importe o Thor para o banco de dados"
- "Quais heróis fazem parte dos X-Men?"

### 🧪 Testando o MCP Server via terminal

```bash
python mcp_server.py
```

O servidor fica aguardando conexões via `stdio`. Em uso normal ele é gerenciado automaticamente pelo cliente MCP.

### 🔍 Diferença entre API REST e MCP Server

|                       | API REST /chat/                       | MCP Server                              |
|-----------------------|----------------------------------------|-----------------------------------------|
| Acesso via           | HTTP (Postman, frontend, curl)        | Clientes MCP (Claude Desktop, Cursor)   |
| IA utilizada         | Groq LLaMA configurada no projeto     | IA do próprio cliente (Claude, etc.)    |
| Protocolo            | HTTP / JSON                           | `stdio` — Model Context Protocol        |
| Uso ideal            | Integração com sistemas e frontends   | Uso direto pelo desenvolvedor           |

---

## 🧪 Exemplos de Uso

### Fluxo típico

```bash
# 1. Suba a API
uvicorn app.main:app --reload

# 2. Importe heróis da API externa
curl -X POST http://localhost:8000/import/search/batman
curl -X POST http://localhost:8000/import/search/spider
curl -X POST http://localhost:8000/import/search/thor
curl -X POST http://localhost:8000/import/search/hulk

# 3. Pergunte para a IA
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual dos Avengers tem maior força?"}'
```

### Criar herói manualmente via CRUD

```bash
curl -X POST http://localhost:8000/heroes/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Homem-Aranha",
    "external_id": "manual_spider_br",
    "powerstats": {
      "intelligence": 90,
      "strength": 55,
      "speed": 67,
      "durability": 75,
      "power": 74,
      "combat": 85
    },
    "biography": {
      "full_name": "Peter Parker",
      "publisher": "Marvel Comics",
      "alignment": "good",
      "aliases": ["Friendly Neighborhood Spider-Man", "Web-Slinger"]
    },
    "appearance": {
      "gender": "Male",
      "race": "Human",
      "eye_color": "Hazel",
      "hair_color": "Brown",
      "heights": ["5 10", "178 cm"],
      "weights": ["167 lb", "76 kg"]
    },
    "work": {
      "occupation": "Freelance photographer",
      "base": "New York City"
    },
    "connections": {
      "group_affiliation": "Avengers, Spider-Man Family",
      "relatives": "May Parker (aunt), Ben Parker (uncle, deceased)"
    }
  }'
```

---

## 🧯 Resolução de Problemas

### `Router.__init__() got an unexpected keyword argument 'on_startup'`

Conflito de versão entre **FastAPI** e **Starlette**.

```bash
pip install -r requirements.txt --force-reinstall
```

### `Client.__init__() got an unexpected keyword argument 'proxies'`

Versão do **httpx** incompatível com o OpenAI SDK.

```bash
pip install "httpx>=0.27.0,<0.28.0"
```

### `Redirect response '302 Found'`

A URL correta da SuperheroAPI é:

```text
https://www.superheroapi.com/api.php/{token}
```

Certifique-se de que `follow_redirects=True` está configurado no cliente `httpx`.

### `tool_use_failed`

O modelo está com dificuldades em gerar chamadas de ferramentas. Use:

```env
GROQ_MODEL=llama3-groq-70b-8192-tool-use-preview
```

### `'Settings' object has no attribute 'GROQ_API_KEY'`

Os nomes das variáveis estão inconsistentes. Verifique se `.env`, `config.py` e `grok_service.py` usam **exatamente**:

- `GROQ_API_KEY`
- `GROQ_MODEL`
- `TOKEN_API_HEROES` -- Este token voce consegue gerar no site "https://superheroapi.com/"

---

## 📄 Licença

Este projeto é distribuído sob a licença **MIT**.