# app/models.py
from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Superhero(Base):
    """
    Tabela principal. Cada herói importado da API externa
    tem um registro aqui, com external_id sendo o ID de lá.
    """
    __tablename__ = "superheroes"

    id          = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(20), unique=True, nullable=False, index=True)
    name        = Column(String(150), nullable=False, index=True)
    image_url   = Column(String(500), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # relacionamentos 1:1 — uselist=False significa um único objeto, não lista
    powerstats  = relationship("SuperheroPowerstats", back_populates="superhero", uselist=False, cascade="all, delete-orphan")
    biography   = relationship("SuperheroBiography",  back_populates="superhero", uselist=False, cascade="all, delete-orphan")
    appearance  = relationship("SuperheroAppearance", back_populates="superhero", uselist=False, cascade="all, delete-orphan")
    work        = relationship("SuperheroWork",        back_populates="superhero", uselist=False, cascade="all, delete-orphan")
    connections = relationship("SuperheroConnections", back_populates="superhero", uselist=False, cascade="all, delete-orphan")


class SuperheroPowerstats(Base):
    """Stats numéricos de 0 a 100 vindos da API externa."""
    __tablename__ = "superhero_powerstats"
    __table_args__ = (UniqueConstraint("superhero_id"),)

    id           = Column(Integer, primary_key=True)
    superhero_id = Column(Integer, ForeignKey("superheroes.id", ondelete="CASCADE"), nullable=False)
    intelligence = Column(Integer, nullable=True)
    strength     = Column(Integer, nullable=True)
    speed        = Column(Integer, nullable=True)
    durability   = Column(Integer, nullable=True)
    power        = Column(Integer, nullable=True)
    combat       = Column(Integer, nullable=True)

    superhero = relationship("Superhero", back_populates="powerstats")


class SuperheroBiography(Base):
    """Dados biográficos do herói."""
    __tablename__ = "superhero_biography"
    __table_args__ = (UniqueConstraint("superhero_id"),)

    id               = Column(Integer, primary_key=True)
    superhero_id     = Column(Integer, ForeignKey("superheroes.id", ondelete="CASCADE"), nullable=False)
    full_name        = Column(String(200), nullable=True)
    alter_egos       = Column(Text, nullable=True)
    place_of_birth   = Column(String(300), nullable=True)
    first_appearance = Column(String(200), nullable=True)
    publisher        = Column(String(150), nullable=True, index=True)
    alignment        = Column(String(50), nullable=True)

    superhero = relationship("Superhero", back_populates="biography")
    # 1:N — um herói pode ter vários aliases
    aliases   = relationship("SuperheroAlias", back_populates="biography", cascade="all, delete-orphan")


class SuperheroAlias(Base):
    """
    Aliases do herói separados em tabela própria
    porque a API retorna um array de strings.
    """
    __tablename__ = "superhero_aliases"

    id           = Column(Integer, primary_key=True)
    biography_id = Column(Integer, ForeignKey("superhero_biography.id", ondelete="CASCADE"), nullable=False)
    alias        = Column(String(200), nullable=False)

    biography = relationship("SuperheroBiography", back_populates="aliases")


class SuperheroAppearance(Base):
    """Características físicas do herói."""
    __tablename__ = "superhero_appearance"
    __table_args__ = (UniqueConstraint("superhero_id"),)

    id           = Column(Integer, primary_key=True)
    superhero_id = Column(Integer, ForeignKey("superheroes.id", ondelete="CASCADE"), nullable=False)
    gender       = Column(String(50), nullable=True)
    race         = Column(String(100), nullable=True)
    eye_color    = Column(String(50), nullable=True)
    hair_color   = Column(String(50), nullable=True)

    superhero = relationship("Superhero", back_populates="appearance")
    # 1:N porque a API retorna ["5'10", "178 cm"]
    heights   = relationship("SuperheroHeight", back_populates="appearance", cascade="all, delete-orphan")
    weights   = relationship("SuperheroWeight", back_populates="appearance", cascade="all, delete-orphan")


class SuperheroHeight(Base):
    """Cada valor de altura em unidade separada (imperial e métrico)."""
    __tablename__ = "superhero_heights"

    id            = Column(Integer, primary_key=True)
    appearance_id = Column(Integer, ForeignKey("superhero_appearance.id", ondelete="CASCADE"), nullable=False)
    value         = Column(String(50), nullable=False)

    appearance = relationship("SuperheroAppearance", back_populates="heights")


class SuperheroWeight(Base):
    """Cada valor de peso em unidade separada (imperial e métrico)."""
    __tablename__ = "superhero_weights"

    id            = Column(Integer, primary_key=True)
    appearance_id = Column(Integer, ForeignKey("superhero_appearance.id", ondelete="CASCADE"), nullable=False)
    value         = Column(String(50), nullable=False)

    appearance = relationship("SuperheroAppearance", back_populates="weights")


class SuperheroWork(Base):
    """Ocupação e base de operações do herói."""
    __tablename__ = "superhero_work"
    __table_args__ = (UniqueConstraint("superhero_id"),)

    id           = Column(Integer, primary_key=True)
    superhero_id = Column(Integer, ForeignKey("superheroes.id", ondelete="CASCADE"), nullable=False)
    occupation   = Column(String(300), nullable=True)
    base         = Column(Text, nullable=True)

    superhero = relationship("Superhero", back_populates="work")


class SuperheroConnections(Base):
    """Times e familiares do herói."""
    __tablename__ = "superhero_connections"
    __table_args__ = (UniqueConstraint("superhero_id"),)

    id                = Column(Integer, primary_key=True)
    superhero_id      = Column(Integer, ForeignKey("superheroes.id", ondelete="CASCADE"), nullable=False)
    group_affiliation = Column(Text, nullable=True)
    relatives         = Column(Text, nullable=True)

    superhero = relationship("Superhero", back_populates="connections")