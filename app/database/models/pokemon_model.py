from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PokemonModel(Base):
    __tablename__ = "pokemon"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    national_pokedex_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    stats: Mapped["PokemonStatsModel"] = relationship(
        back_populates="pokemon",
        uselist=False,
        cascade="all, delete-orphan",
    )
    types: Mapped[list["PokemonTypeModel"]] = relationship(
        back_populates="pokemon",
        cascade="all, delete-orphan",
    )
    abilities: Mapped[list["PokemonAbilityModel"]] = relationship(
        back_populates="pokemon",
        cascade="all, delete-orphan",
    )
    evolution: Mapped["PokemonEvolutionModel"] = relationship(
        back_populates="pokemon",
        uselist=False,
        cascade="all, delete-orphan",
    )
    gender: Mapped["PokemonGenderModel"] = relationship(
        back_populates="pokemon",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PokemonStatsModel(Base):
    __tablename__ = "pokemon_stats"

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"),
        primary_key=True,
    )
    hp: Mapped[int] = mapped_column(Integer, nullable=False)
    attack: Mapped[int] = mapped_column(Integer, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, nullable=False)
    special_attack: Mapped[int] = mapped_column(Integer, nullable=False)
    special_defense: Mapped[int] = mapped_column(Integer, nullable=False)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)

    pokemon: Mapped[PokemonModel] = relationship(back_populates="stats")


class PokemonTypeModel(Base):
    __tablename__ = "pokemon_types"

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"),
        primary_key=True,
    )
    type: Mapped[str] = mapped_column(String(30), primary_key=True)

    pokemon: Mapped[PokemonModel] = relationship(back_populates="types")


class PokemonAbilityModel(Base):
    __tablename__ = "pokemon_abilities"
    __table_args__ = (
        UniqueConstraint("pokemon_id", "name", name="uq_pokemon_ability_name"),
    )

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(120), primary_key=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    pokemon: Mapped[PokemonModel] = relationship(back_populates="abilities")


class PokemonEvolutionModel(Base):
    __tablename__ = "pokemon_evolution"

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"),
        primary_key=True,
    )
    prev_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    next_name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    pokemon: Mapped[PokemonModel] = relationship(back_populates="evolution")


class PokemonGenderModel(Base):
    __tablename__ = "pokemon_gender"

    pokemon_id: Mapped[int] = mapped_column(
        ForeignKey("pokemon.id", ondelete="CASCADE"),
        primary_key=True,
    )
    male: Mapped[float] = mapped_column(Float, nullable=False)
    female: Mapped[float] = mapped_column(Float, nullable=False)

    pokemon: Mapped[PokemonModel] = relationship(back_populates="gender")

