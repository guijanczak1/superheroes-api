# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import heroes, import_heroes, chat

# Cria todas as tabelas no banco se ainda não existirem
# Em produção prefira usar Alembic para migrations
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Superhero API",
    description="""
    API REST para gerenciamento de super-heróis.

    ## Funcionalidades
    - **CRUD completo** de heróis com dados relacionais
    - **Importação** direto da SuperheroAPI externa
    - **Chat com IA** via Grok com acesso ao banco de dados
    - **MCP Server** disponível para clientes externos (mcp_server.py)
    """,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(heroes.router)
app.include_router(import_heroes.router)
app.include_router(chat.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "online", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}