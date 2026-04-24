# mcp_server.py
"""
Servidor MCP standalone para o banco de super-heróis.

Como usar com Claude Desktop — adicione em claude_desktop_config.json:
{
  "mcpServers": {
    "superhero-db": {
      "command": "python",
      "args": ["/caminho/absoluto/para/mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/superhero_db"
      }
    }
  }
}

Como testar via terminal:
    python mcp_server.py
"""

import asyncio
import json
import os
import sys

# garante que o diretório raiz está no path para importar app.*
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrada. Configure o arquivo .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import app.crud as crud
from app.services.superhero_api_service import _model_to_response

# ----------------------------------------------------------------
# Instância do servidor MCP
# ----------------------------------------------------------------
server = Server("superhero-mcp-server")


# ----------------------------------------------------------------
# Lista de ferramentas expostas pelo servidor
# ----------------------------------------------------------------
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_all_heroes",
            description="Retorna todos os super-heróis cadastrados no banco de dados Postgres.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Máximo de registros a retornar. Padrão: 50.",
                        "default": 50
                    }
                }
            }
        ),
        types.Tool(
            name="search_by_name",
            description="Busca heróis pelo nome (busca parcial e case-insensitive).",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome ou parte do nome do herói"
                    }
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="get_hero_by_id",
            description="Retorna um herói completo pelo ID interno do banco.",
            inputSchema={
                "type": "object",
                "properties": {
                    "hero_id": {
                        "type": "integer",
                        "description": "ID interno do herói no banco de dados"
                    }
                },
                "required": ["hero_id"]
            }
        ),
        types.Tool(
            name="get_by_publisher",
            description="Retorna todos os heróis de uma editora (Marvel, DC, etc).",
            inputSchema={
                "type": "object",
                "properties": {
                    "publisher": {
                        "type": "string",
                        "description": "Nome da editora"
                    }
                },
                "required": ["publisher"]
            }
        ),
        types.Tool(
            name="get_by_alignment",
            description="Retorna heróis pelo alinhamento moral.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alignment": {
                        "type": "string",
                        "enum": ["good", "bad", "neutral"],
                        "description": "Alinhamento: good, bad ou neutral"
                    }
                },
                "required": ["alignment"]
            }
        ),
        types.Tool(
            name="count_heroes",
            description="Retorna o total de heróis cadastrados no banco.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="import_hero",
            description="Busca e importa heróis da SuperheroAPI externa para o banco.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nome do herói para buscar na API externa (ex: batman, spider, thor)"
                    }
                },
                "required": ["query"]
            }
        )
    ]


# ----------------------------------------------------------------
# Handler de execução das ferramentas
# ----------------------------------------------------------------
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """
    Cada ferramenta abre sua própria sessão de banco para garantir
    isolamento e evitar sessões abertas desnecessariamente.
    """
    db = SessionLocal()
    try:
        result = await _execute(name, arguments, db)
        return [types.TextContent(type="text", text=result)]
    except Exception as e:
        error = json.dumps({"error": str(e)}, ensure_ascii=False)
        return [types.TextContent(type="text", text=error)]
    finally:
        db.close()


async def _execute(name: str, args: dict, db) -> str:
    """Roteia a chamada para a função CRUD correta."""

    if name == "get_all_heroes":
        limit = args.get("limit", 50)
        heroes = crud.get_all(db, limit=limit)
        data = [_model_to_response(h).model_dump() for h in heroes]
        return json.dumps(data, default=str, ensure_ascii=False)

    if name == "search_by_name":
        heroes = crud.search_by_name(db, args["name"])
        data = [_model_to_response(h).model_dump() for h in heroes]
        return json.dumps(data, default=str, ensure_ascii=False)

    if name == "get_hero_by_id":
        hero = crud.get_by_id(db, args["hero_id"])
        if not hero:
            return json.dumps({"error": f"Herói com id={args['hero_id']} não encontrado"})
        return json.dumps(_model_to_response(hero).model_dump(), default=str, ensure_ascii=False)

    if name == "get_by_publisher":
        heroes = crud.get_by_publisher(db, args["publisher"])
        data = [_model_to_response(h).model_dump() for h in heroes]
        return json.dumps(data, default=str, ensure_ascii=False)

    if name == "get_by_alignment":
        heroes = crud.get_by_alignment(db, args["alignment"])
        data = [_model_to_response(h).model_dump() for h in heroes]
        return json.dumps(data, default=str, ensure_ascii=False)

    if name == "count_heroes":
        total = crud.count_all(db)
        return json.dumps({"total_heroes": total})

    if name == "import_hero":
        # importação usa o service que chama a API externa
        from app.services.superhero_api_service import SuperheroAPIService
        service = SuperheroAPIService(db)
        result = service.search_and_import(args["query"])
        return json.dumps(result.model_dump(), default=str, ensure_ascii=False)

    return json.dumps({"error": f"Ferramenta '{name}' não reconhecida"})


# ----------------------------------------------------------------
# Entrypoint do servidor MCP
# ----------------------------------------------------------------
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())