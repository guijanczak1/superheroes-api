# app/crud.py
from sqlalchemy.orm import Session
from typing import Optional, List

from app.models import (
    Superhero, SuperheroPowerstats, SuperheroBiography,
    SuperheroAlias, SuperheroAppearance, SuperheroHeight,
    SuperheroWeight, SuperheroWork, SuperheroConnections
)
from app.schemas import SuperheroCreate, SuperheroUpdate


# ================================================================
# Funções auxiliares de mapeamento
# ================================================================

def _build_powerstats(data) -> SuperheroPowerstats:
    return SuperheroPowerstats(
        intelligence=data.intelligence,
        strength=    data.strength,
        speed=       data.speed,
        durability=  data.durability,
        power=       data.power,
        combat=      data.combat,
    )


def _build_biography(data) -> SuperheroBiography:
    bio = SuperheroBiography(
        full_name=       data.full_name,
        alter_egos=      data.alter_egos,
        place_of_birth=  data.place_of_birth,
        first_appearance=data.first_appearance,
        publisher=       data.publisher,
        alignment=       data.alignment,
    )
    if data.aliases:
        bio.aliases = [SuperheroAlias(alias=a) for a in data.aliases if a]
    return bio


def _build_appearance(data) -> SuperheroAppearance:
    app_obj = SuperheroAppearance(
        gender=    data.gender,
        race=      data.race,
        eye_color= data.eye_color,
        hair_color=data.hair_color,
    )
    if data.heights:
        app_obj.heights = [SuperheroHeight(value=h) for h in data.heights if h]
    if data.weights:
        app_obj.weights = [SuperheroWeight(value=w) for w in data.weights if w]
    return app_obj


def _build_work(data) -> SuperheroWork:
    return SuperheroWork(occupation=data.occupation, base=data.base)


def _build_connections(data) -> SuperheroConnections:
    return SuperheroConnections(
        group_affiliation=data.group_affiliation,
        relatives=        data.relatives,
    )


# ================================================================
# CREATE
# ================================================================

def create_hero(db: Session, hero_in: SuperheroCreate) -> Superhero:
    """
    Cria um herói com todos os relacionamentos em uma única transação.
    O flush() garante que o ID do herói é gerado antes dos filhos.
    """
    hero = Superhero(
        name=        hero_in.name,
        external_id= hero_in.external_id or f"manual_{hero_in.name.lower().replace(' ', '_')}",
        image_url=   hero_in.image_url,
    )

    if hero_in.powerstats:
        hero.powerstats = _build_powerstats(hero_in.powerstats)
    if hero_in.biography:
        hero.biography = _build_biography(hero_in.biography)
    if hero_in.appearance:
        hero.appearance = _build_appearance(hero_in.appearance)
    if hero_in.work:
        hero.work = _build_work(hero_in.work)
    if hero_in.connections:
        hero.connections = _build_connections(hero_in.connections)

    db.add(hero)
    db.commit()
    db.refresh(hero)
    return hero


# ================================================================
# READ
# ================================================================

def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Superhero]:
    return db.query(Superhero).offset(skip).limit(limit).all()


def get_by_id(db: Session, hero_id: int) -> Optional[Superhero]:
    return db.query(Superhero).filter(Superhero.id == hero_id).first()


def get_by_external_id(db: Session, external_id: str) -> Optional[Superhero]:
    return db.query(Superhero).filter(Superhero.external_id == external_id).first()


def search_by_name(db: Session, name: str) -> List[Superhero]:
    """Busca parcial case-insensitive pelo nome."""
    return db.query(Superhero).filter(
        Superhero.name.ilike(f"%{name}%")
    ).all()


def get_by_publisher(db: Session, publisher: str) -> List[Superhero]:
    return (
        db.query(Superhero)
        .join(Superhero.biography)
        .filter(SuperheroBiography.publisher.ilike(f"%{publisher}%"))
        .all()
    )


def get_by_alignment(db: Session, alignment: str) -> List[Superhero]:
    return (
        db.query(Superhero)
        .join(Superhero.biography)
        .filter(SuperheroBiography.alignment.ilike(alignment))
        .all()
    )


def count_all(db: Session) -> int:
    return db.query(Superhero).count()


# ================================================================
# UPDATE
# ================================================================

def update_hero(db: Session, hero_id: int, hero_in: SuperheroUpdate) -> Optional[Superhero]:
    """
    Atualiza apenas os campos enviados.
    Para relacionamentos, faz delete + insert para simplificar.
    """
    hero = get_by_id(db, hero_id)
    if not hero:
        return None

    if hero_in.name is not None:
        hero.name = hero_in.name
    if hero_in.image_url is not None:
        hero.image_url = hero_in.image_url

    if hero_in.powerstats is not None:
        if hero.powerstats:
            ps = hero.powerstats
            ps.intelligence = hero_in.powerstats.intelligence
            ps.strength     = hero_in.powerstats.strength
            ps.speed        = hero_in.powerstats.speed
            ps.durability   = hero_in.powerstats.durability
            ps.power        = hero_in.powerstats.power
            ps.combat       = hero_in.powerstats.combat
        else:
            hero.powerstats = _build_powerstats(hero_in.powerstats)

    if hero_in.biography is not None:
        if hero.biography:
            bio = hero.biography
            bio.full_name        = hero_in.biography.full_name
            bio.alter_egos       = hero_in.biography.alter_egos
            bio.place_of_birth   = hero_in.biography.place_of_birth
            bio.first_appearance = hero_in.biography.first_appearance
            bio.publisher        = hero_in.biography.publisher
            bio.alignment        = hero_in.biography.alignment
            # recria aliases
            for alias in bio.aliases:
                db.delete(alias)
            db.flush()
            if hero_in.biography.aliases:
                bio.aliases = [SuperheroAlias(alias=a) for a in hero_in.biography.aliases if a]
        else:
            hero.biography = _build_biography(hero_in.biography)

    if hero_in.appearance is not None:
        if hero.appearance:
            app_obj = hero.appearance
            app_obj.gender    = hero_in.appearance.gender
            app_obj.race      = hero_in.appearance.race
            app_obj.eye_color = hero_in.appearance.eye_color
            app_obj.hair_color = hero_in.appearance.hair_color
            for h in app_obj.heights:
                db.delete(h)
            for w in app_obj.weights:
                db.delete(w)
            db.flush()
            if hero_in.appearance.heights:
                app_obj.heights = [SuperheroHeight(value=h) for h in hero_in.appearance.heights]
            if hero_in.appearance.weights:
                app_obj.weights = [SuperheroWeight(value=w) for w in hero_in.appearance.weights]
        else:
            hero.appearance = _build_appearance(hero_in.appearance)

    if hero_in.work is not None:
        if hero.work:
            hero.work.occupation = hero_in.work.occupation
            hero.work.base       = hero_in.work.base
        else:
            hero.work = _build_work(hero_in.work)

    if hero_in.connections is not None:
        if hero.connections:
            hero.connections.group_affiliation = hero_in.connections.group_affiliation
            hero.connections.relatives         = hero_in.connections.relatives
        else:
            hero.connections = _build_connections(hero_in.connections)

    db.commit()
    db.refresh(hero)
    return hero


# ================================================================
# DELETE
# ================================================================

def delete_hero(db: Session, hero_id: int) -> bool:
    """
    O cascade="all, delete-orphan" nos relacionamentos garante
    que todos os filhos são deletados junto com o herói.
    """
    hero = get_by_id(db, hero_id)
    if not hero:
        return False
    db.delete(hero)
    db.commit()
    return True