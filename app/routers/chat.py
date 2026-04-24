from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.groq_service import GroqService

router = APIRouter(prefix="/chat", tags=["AI Chat - Groq"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Converse com a IA Grok sobre os heróis cadastrados.

    Exemplos de perguntas:
    - 'Quais heróis da Marvel temos no banco?'
    - 'Me dê detalhes sobre o Batman'
    - 'Quantos heróis estão cadastrados?'
    - 'Quais são os vilões (alignment bad)?'
    - 'Qual herói tem maior inteligência?'
    """
    service = GroqService(db)
    response_text, tools_used = service.chat(request.message)
    return ChatResponse(response=response_text, tools_used=tools_used)