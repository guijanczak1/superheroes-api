import json
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import settings
from app.models import (
    Superhero, SuperheroPowerstats, SuperheroBiography,
    SuperheroAlias, SuperheroAppearance, SuperheroHeight,
    SuperheroWeight, SuperheroWork, SuperheroConnections
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_heroes",
            "description": "Busca heróis com filtros opcionais de nome, publisher ou alignment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name":      {"type": "string", "description": "Parte do nome do herói"},
                    "publisher": {"type": "string", "description": "Editora (Marvel Comics, DC Comics)"},
                    "alignment": {"type": "string", "enum": ["good", "bad", "neutral"]},
                    "limit":     {"type": "integer", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_full_hero_profile",
            "description": "Retorna todos os dados de um herói pelo ID: stats, bio, aparência, trabalho e conexões.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hero_id": {"type": "integer", "description": "ID interno do herói"}
                },
                "required": ["hero_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_heroes_by_stat",
            "description": "Ranking dos heróis com maior valor em um atributo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "stat":  {"type": "string", "enum": ["intelligence", "strength", "speed", "durability", "power", "combat"]},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["stat"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_heroes_stats",
            "description": "Compara power stats de dois heróis lado a lado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hero_id_1": {"type": "integer"},
                    "hero_id_2": {"type": "integer"}
                },
                "required": ["hero_id_1", "hero_id_2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_heroes_by_group",
            "description": "Busca heróis por time ou grupo (Avengers, X-Men, Justice League).",
            "parameters": {
                "type": "object",
                "properties": {
                    "group": {"type": "string", "description": "Nome do grupo ou time"}
                },
                "required": ["group"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_heroes_by_race",
            "description": "Busca heróis por raça (Human, Mutant, Alien, God, etc).",
            "parameters": {
                "type": "object",
                "properties": {
                    "race": {"type": "string"}
                },
                "required": ["race"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_heroes",
            "description": "Retorna o total de heróis no banco.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

class GroqService:

    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = settings.GROQ_MODEL
        self.tools = TOOLS

    def _run_tool(self, name: str, args: dict) -> str:
        try:
            result = self._dispatch(name, args)
            return json.dumps(result, default=str, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _dispatch(self, name: str, args: dict):

        if name == "get_all_heroes":
            rows = (
                self.db.query(Superhero)
                .offset(args.get("skip", 0))
                .limit(args.get("limit", 100))
                .all()
            )
            return [{"id": h.id, "name": h.name, "external_id": h.external_id, "image_url": h.image_url} for h in rows]

        if name == "get_hero_by_id":
            h = self.db.query(Superhero).filter(Superhero.id == args["hero_id"]).first()
            if not h:
                return {"error": "Herói não encontrado"}
            return {"id": h.id, "name": h.name, "external_id": h.external_id, "image_url": h.image_url}

        if name == "search_hero_by_name":
            rows = self.db.query(Superhero).filter(
                Superhero.name.ilike(f"%{args['name']}%")
            ).all()
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "count_heroes":
            total = self.db.query(func.count(Superhero.id)).scalar()
            return {"total_heroes": total}

        if name == "get_powerstats_by_hero":
            ps = self.db.query(SuperheroPowerstats).filter(
                SuperheroPowerstats.superhero_id == args["hero_id"]
            ).first()
            if not ps:
                return {"error": "Powerstats não encontrados"}
            return {
                "hero_id":      ps.superhero_id,
                "intelligence": ps.intelligence,
                "strength":     ps.strength,
                "speed":        ps.speed,
                "durability":   ps.durability,
                "power":        ps.power,
                "combat":       ps.combat,
            }

        if name == "get_top_heroes_by_stat":
            stat_col = getattr(SuperheroPowerstats, args["stat"], None)
            if stat_col is None:
                return {"error": f"Atributo '{args['stat']}' inválido"}
            rows = (
                self.db.query(Superhero.id, Superhero.name, stat_col)
                .join(SuperheroPowerstats, Superhero.id == SuperheroPowerstats.superhero_id)
                .filter(stat_col.isnot(None))
                .order_by(stat_col.desc())
                .limit(args.get("limit", 5))
                .all()
            )
            return [{"id": r[0], "name": r[1], args["stat"]: r[2]} for r in rows]

        if name == "get_all_powerstats":
            rows = (
                self.db.query(Superhero.id, Superhero.name, SuperheroPowerstats)
                .join(SuperheroPowerstats, Superhero.id == SuperheroPowerstats.superhero_id)
                .limit(args.get("limit", 100))
                .all()
            )
            return [
                {
                    "id": r[0], "name": r[1],
                    "intelligence": r[2].intelligence, "strength": r[2].strength,
                    "speed": r[2].speed, "durability": r[2].durability,
                    "power": r[2].power, "combat": r[2].combat,
                }
                for r in rows
            ]

        if name == "get_biography_by_hero":
            bio = self.db.query(SuperheroBiography).filter(
                SuperheroBiography.superhero_id == args["hero_id"]
            ).first()
            if not bio:
                return {"error": "Biografia não encontrada"}
            return {
                "hero_id":        bio.superhero_id,
                "full_name":      bio.full_name,
                "alter_egos":     bio.alter_egos,
                "place_of_birth": bio.place_of_birth,
                "first_appearance": bio.first_appearance,
                "publisher":      bio.publisher,
                "alignment":      bio.alignment,
            }

        if name == "get_heroes_by_publisher":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroBiography)
                .filter(SuperheroBiography.publisher.ilike(f"%{args['publisher']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "get_heroes_by_alignment":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroBiography)
                .filter(SuperheroBiography.alignment.ilike(args["alignment"]))
                .all()
            )
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "search_hero_by_real_name":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroBiography)
                .filter(SuperheroBiography.full_name.ilike(f"%{args['real_name']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name, "real_name": h.biography.full_name} for h in rows]

        if name == "list_publishers":
            rows = (
                self.db.query(SuperheroBiography.publisher)
                .filter(SuperheroBiography.publisher.isnot(None))
                .distinct()
                .all()
            )
            return [r[0] for r in rows]

        if name == "get_aliases_by_hero":
            rows = (
                self.db.query(SuperheroAlias)
                .join(SuperheroBiography)
                .filter(SuperheroBiography.superhero_id == args["hero_id"])
                .all()
            )
            return [{"id": a.id, "alias": a.alias} for a in rows]

        if name == "search_hero_by_alias":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroBiography)
                .join(SuperheroAlias)
                .filter(SuperheroAlias.alias.ilike(f"%{args['alias']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "get_appearance_by_hero":
            ap = self.db.query(SuperheroAppearance).filter(
                SuperheroAppearance.superhero_id == args["hero_id"]
            ).first()
            if not ap:
                return {"error": "Dados de aparência não encontrados"}
            return {
                "hero_id":   ap.superhero_id,
                "gender":    ap.gender,
                "race":      ap.race,
                "eye_color": ap.eye_color,
                "hair_color": ap.hair_color,
            }

        if name == "get_heroes_by_race":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroAppearance)
                .filter(SuperheroAppearance.race.ilike(f"%{args['race']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "get_heroes_by_gender":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroAppearance)
                .filter(SuperheroAppearance.gender.ilike(args["gender"]))
                .all()
            )
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "list_races":
            rows = (
                self.db.query(SuperheroAppearance.race)
                .filter(SuperheroAppearance.race.isnot(None))
                .distinct()
                .all()
            )
            return [r[0] for r in rows]

        if name == "get_height_and_weight_by_hero":
            ap = self.db.query(SuperheroAppearance).filter(
                SuperheroAppearance.superhero_id == args["hero_id"]
            ).first()
            if not ap:
                return {"error": "Dados não encontrados"}
            return {
                "hero_id": ap.superhero_id,
                "heights": [h.value for h in ap.heights],
                "weights": [w.value for w in ap.weights],
            }

        if name == "get_work_by_hero":
            w = self.db.query(SuperheroWork).filter(
                SuperheroWork.superhero_id == args["hero_id"]
            ).first()
            if not w:
                return {"error": "Dados de trabalho não encontrados"}
            return {
                "hero_id":    w.superhero_id,
                "occupation": w.occupation,
                "base":       w.base,
            }

        if name == "search_heroes_by_base":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroWork)
                .filter(SuperheroWork.base.ilike(f"%{args['base']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name, "base": h.work.base} for h in rows]

        if name == "search_heroes_by_occupation":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroWork)
                .filter(SuperheroWork.occupation.ilike(f"%{args['occupation']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name, "occupation": h.work.occupation} for h in rows]

        if name == "get_connections_by_hero":
            c = self.db.query(SuperheroConnections).filter(
                SuperheroConnections.superhero_id == args["hero_id"]
            ).first()
            if not c:
                return {"error": "Conexões não encontradas"}
            return {
                "hero_id":           c.superhero_id,
                "group_affiliation": c.group_affiliation,
                "relatives":         c.relatives,
            }

        if name == "search_heroes_by_group":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroConnections)
                .filter(SuperheroConnections.group_affiliation.ilike(f"%{args['group']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "search_heroes_by_relative":
            rows = (
                self.db.query(Superhero)
                .join(SuperheroConnections)
                .filter(SuperheroConnections.relatives.ilike(f"%{args['relative']}%"))
                .all()
            )
            return [{"id": h.id, "name": h.name} for h in rows]

        if name == "get_full_hero_profile":
            h = self.db.query(Superhero).filter(Superhero.id == args["hero_id"]).first()
            if not h:
                return {"error": "Herói não encontrado"}
            return {
                "id":         h.id,
                "name":       h.name,
                "image_url":  h.image_url,
                "powerstats": {
                    "intelligence": h.powerstats.intelligence,
                    "strength":     h.powerstats.strength,
                    "speed":        h.powerstats.speed,
                    "durability":   h.powerstats.durability,
                    "power":        h.powerstats.power,
                    "combat":       h.powerstats.combat,
                } if h.powerstats else None,
                "biography": {
                    "full_name":        h.biography.full_name,
                    "alter_egos":       h.biography.alter_egos,
                    "aliases":          [a.alias for a in h.biography.aliases],
                    "place_of_birth":   h.biography.place_of_birth,
                    "first_appearance": h.biography.first_appearance,
                    "publisher":        h.biography.publisher,
                    "alignment":        h.biography.alignment,
                } if h.biography else None,
                "appearance": {
                    "gender":     h.appearance.gender,
                    "race":       h.appearance.race,
                    "eye_color":  h.appearance.eye_color,
                    "hair_color": h.appearance.hair_color,
                    "heights":    [x.value for x in h.appearance.heights],
                    "weights":    [x.value for x in h.appearance.weights],
                } if h.appearance else None,
                "work": {
                    "occupation": h.work.occupation,
                    "base":       h.work.base,
                } if h.work else None,
                "connections": {
                    "group_affiliation": h.connections.group_affiliation,
                    "relatives":         h.connections.relatives,
                } if h.connections else None,
            }

        if name == "compare_heroes_stats":
            def get_stats(hero_id):
                h = self.db.query(Superhero).filter(Superhero.id == hero_id).first()
                if not h:
                    return {"error": f"Herói {hero_id} não encontrado"}
                ps = h.powerstats
                return {
                    "id": h.id, "name": h.name,
                    "intelligence": ps.intelligence if ps else None,
                    "strength":     ps.strength     if ps else None,
                    "speed":        ps.speed        if ps else None,
                    "durability":   ps.durability   if ps else None,
                    "power":        ps.power        if ps else None,
                    "combat":       ps.combat       if ps else None,
                }
            return {
                "hero_1": get_stats(args["hero_id_1"]),
                "hero_2": get_stats(args["hero_id_2"]),
            }

        return {"error": f"Tool '{name}' não reconhecida"}

    def chat(self, user_message: str) -> tuple[str, list[str]]:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um assistente especializado em super-heróis com acesso completo "
                    "ao banco de dados. Você pode consultar heróis, power stats, biografias, "
                    "aliases, aparências, alturas, pesos, trabalhos e conexões. "
                    "Sempre use as ferramentas disponíveis para buscar dados antes de responder. "
                    "Quando não souber o ID de um herói, use search_hero_by_name primeiro. "
                    "Responda no mesmo idioma da pergunta do usuário."
                )
            },
            {"role": "user", "content": user_message}
        ]

        tools_used = []

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto"
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                for call in choice.message.tool_calls:
                    tool_name = call.function.name
                    tool_args = json.loads(call.function.arguments)
                    tools_used.append(tool_name)
                    result = self._run_tool(tool_name, tool_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result
                    })
            else:
                return choice.message.content, tools_used