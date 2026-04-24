# app/services/superhero_api_service.py
import httpx
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.schemas import (
    SuperheroAPIResponseDTO, SuperheroExternalDTO,
    ImportResultResponse, SuperheroResponse,
    PowerstatsResponse, BiographyResponse, AliasResponse,
    AppearanceResponse, WorkResponse, ConnectionsResponse,
)
from app.models import (
    Superhero, SuperheroPowerstats, SuperheroBiography,
    SuperheroAlias, SuperheroAppearance, SuperheroHeight,
    SuperheroWeight, SuperheroWork, SuperheroConnections,
)
import app.crud as crud

SUPERHERO_API_BASE = "https://superheroapi.com/api/"


def _safe_int(value) -> int | None:
    """Converte string da API para int. Retorna None se inválido."""
    try:
        return int(value) if value and str(value).strip().lstrip("-").isdigit() else None
    except (ValueError, AttributeError):
        return None


def _map_dto_to_model(dto: SuperheroExternalDTO) -> Superhero:
    """
    Converte o DTO da API externa para o grafo de objetos SQLAlchemy.
    Não persiste nada ainda — apenas monta em memória.
    """
    hero = Superhero(
        external_id=dto.id,
        name=       dto.name,
        image_url=  dto.image.url if dto.image else None,
    )

    if dto.powerstats:
        hero.powerstats = SuperheroPowerstats(
            intelligence=_safe_int(dto.powerstats.intelligence),
            strength=    _safe_int(dto.powerstats.strength),
            speed=       _safe_int(dto.powerstats.speed),
            durability=  _safe_int(dto.powerstats.durability),
            power=       _safe_int(dto.powerstats.power),
            combat=      _safe_int(dto.powerstats.combat),
        )

    if dto.biography:
        bio = dto.biography
        bio_obj = SuperheroBiography(
            full_name=       bio.full_name,
            alter_egos=      bio.alter_egos,
            place_of_birth=  bio.place_of_birth,
            first_appearance=bio.first_appearance,
            publisher=       bio.publisher,
            alignment=       bio.alignment,
        )
        if bio.aliases:
            bio_obj.aliases = [SuperheroAlias(alias=a) for a in bio.aliases if a]
        hero.biography = bio_obj

    if dto.appearance:
        app = dto.appearance
        app_obj = SuperheroAppearance(
            gender=    app.gender,
            race=      app.race,
            eye_color= app.eye_color,
            hair_color=app.hair_color,
        )
        if app.height:
            app_obj.heights = [SuperheroHeight(value=h) for h in app.height if h]
        if app.weight:
            app_obj.weights = [SuperheroWeight(value=w) for w in app.weight if w]
        hero.appearance = app_obj

    if dto.work:
        hero.work = SuperheroWork(
            occupation=dto.work.occupation,
            base=      dto.work.base,
        )

    if dto.connections:
        hero.connections = SuperheroConnections(
            group_affiliation=dto.connections.group_affiliation,
            relatives=        dto.connections.relatives,
        )

    return hero


def _model_to_response(hero: Superhero) -> SuperheroResponse:
    """Converte o model SQLAlchemy para o schema de resposta."""
    return SuperheroResponse(
        id=          hero.id,
        external_id= hero.external_id,
        name=        hero.name,
        image_url=   hero.image_url,
        created_at=  hero.created_at,
        updated_at=  hero.updated_at,
        powerstats=PowerstatsResponse(
            intelligence=hero.powerstats.intelligence,
            strength=    hero.powerstats.strength,
            speed=       hero.powerstats.speed,
            durability=  hero.powerstats.durability,
            power=       hero.powerstats.power,
            combat=      hero.powerstats.combat,
        ) if hero.powerstats else None,
        biography=BiographyResponse(
            full_name=       hero.biography.full_name,
            alter_egos=      hero.biography.alter_egos,
            place_of_birth=  hero.biography.place_of_birth,
            first_appearance=hero.biography.first_appearance,
            publisher=       hero.biography.publisher,
            alignment=       hero.biography.alignment,
            aliases=[AliasResponse(id=a.id, alias=a.alias) for a in hero.biography.aliases],
        ) if hero.biography else None,
        appearance=AppearanceResponse(
            gender=    hero.appearance.gender,
            race=      hero.appearance.race,
            eye_color= hero.appearance.eye_color,
            hair_color=hero.appearance.hair_color,
            heights=   [h.value for h in hero.appearance.heights],
            weights=   [w.value for w in hero.appearance.weights],
        ) if hero.appearance else None,
        work=WorkResponse(
            occupation=hero.work.occupation,
            base=      hero.work.base,
        ) if hero.work else None,
        connections=ConnectionsResponse(
            group_affiliation=hero.connections.group_affiliation,
            relatives=        hero.connections.relatives,
        ) if hero.connections else None,
    )


class SuperheroAPIService:

    def __init__(self, db: Session):
        self.db = db

    def search_and_import(self, query: str) -> ImportResultResponse:
        url = f"{SUPERHERO_API_BASE}/{settings.TOKEN_API_HEROES}/search/{query}"

        with httpx.Client(timeout=15.0, follow_redirects=True) as client:  # <-- follow_redirects=True
            resp = client.get(url)
            resp.raise_for_status()

        api_response = SuperheroAPIResponseDTO.model_validate(resp.json())

        if api_response.response != "success" or not api_response.results:
            return ImportResultResponse(query=query, imported=0, skipped=0, heroes=[])

        imported, skipped = [], 0

        for dto in api_response.results:
            if crud.get_by_external_id(self.db, dto.id):
                skipped += 1
                continue

            hero = _map_dto_to_model(dto)
            self.db.add(hero)
            self.db.flush()
            imported.append(hero)

        self.db.commit()

        for hero in imported:
            self.db.refresh(hero)

        return ImportResultResponse(
            query=query,
            imported=len(imported),
            skipped=skipped,
            heroes=[_model_to_response(h) for h in imported],
        )