# app/routers/import_heroes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ImportResultResponse
from app.services.superhero_api_service import SuperheroAPIService

router = APIRouter(prefix="/import", tags=["Import - External API"])


@router.post("/search/{query}", response_model=ImportResultResponse)
def import_heroes(query: str, db: Session = Depends(get_db)):
    """
    Busca heróis na SuperheroAPI pelo nome e importa para o banco.
    Heróis já existentes (verificado pelo external_id) são ignorados.

    Exemplos: /import/search/batman  |  /import/search/spider  |  /import/search/thor
    """
    service = SuperheroAPIService(db)
    return service.search_and_import(query)