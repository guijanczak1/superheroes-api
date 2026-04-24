from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import SuperheroCreate, SuperheroUpdate, SuperheroResponse
from app.services.superhero_api_service import _model_to_response
import app.crud as crud

router = APIRouter(prefix="/heroes", tags=["CRUD - Heroes"])


@router.post("/", response_model=SuperheroResponse, status_code=201)
def create_hero(hero_in: SuperheroCreate, db: Session = Depends(get_db)):
    """Cria um herói manualmente no banco."""
    hero = crud.create_hero(db, hero_in)
    return _model_to_response(hero)


@router.get("/", response_model=List[SuperheroResponse])
def list_heroes(
    skip:  int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lista todos os heróis com paginação."""
    heroes = crud.get_all(db, skip=skip, limit=limit)
    return [_model_to_response(h) for h in heroes]


@router.get("/search", response_model=List[SuperheroResponse])
def search_heroes(
    name: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Busca heróis pelo nome (parcial, case-insensitive)."""
    heroes = crud.search_by_name(db, name)
    return [_model_to_response(h) for h in heroes]


@router.get("/publisher/{publisher}", response_model=List[SuperheroResponse])
def heroes_by_publisher(publisher: str, db: Session = Depends(get_db)):
    """Filtra heróis por editora."""
    return [_model_to_response(h) for h in crud.get_by_publisher(db, publisher)]


@router.get("/alignment/{alignment}", response_model=List[SuperheroResponse])
def heroes_by_alignment(alignment: str, db: Session = Depends(get_db)):
    """Filtra heróis pelo alinhamento: good, bad ou neutral."""
    return [_model_to_response(h) for h in crud.get_by_alignment(db, alignment)]


@router.get("/{hero_id}", response_model=SuperheroResponse)
def get_hero(hero_id: int, db: Session = Depends(get_db)):
    """Busca um herói pelo ID interno."""
    hero = crud.get_by_id(db, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return _model_to_response(hero)


@router.put("/{hero_id}", response_model=SuperheroResponse)
def update_hero(
    hero_id: int,
    hero_in: SuperheroUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza os dados de um herói. Apenas os campos enviados são alterados."""
    hero = crud.update_hero(db, hero_id, hero_in)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return _model_to_response(hero)


@router.delete("/{hero_id}", status_code=204)
def delete_hero(hero_id: int, db: Session = Depends(get_db)):
    """Remove um herói e todos os dados relacionados."""
    if not crud.delete_hero(db, hero_id):
        raise HTTPException(status_code=404, detail="Hero not found")