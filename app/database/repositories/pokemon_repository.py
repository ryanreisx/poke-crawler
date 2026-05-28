from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.database.models.pokemon_model import (
    PokemonAbilityModel,
    PokemonEvolutionModel,
    PokemonGenderModel,
    PokemonModel,
    PokemonStatsModel,
    PokemonTypeModel,
)
from app.models.ability import Ability
from app.models.pokemon import Pokemon


class PokemonRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, pokemon: Pokemon) -> PokemonModel:
        image_path = self._resolve_image_path_for_upsert(pokemon)

        self._upsert_pokemon_base(pokemon, image_path)
        persisted = self._require_by_national_number(pokemon.national_number)

        self._upsert_stats(persisted.id, pokemon)
        self._upsert_evolution(persisted.id, pokemon)
        self._upsert_gender(persisted.id, pokemon)
        self._sync_types(persisted.id, pokemon.types)
        self._sync_abilities(persisted.id, pokemon.abilities)

        self.session.flush()
        return persisted

    def get_by_national_number(self, national_number: int) -> PokemonModel | None:
        stmt = select(PokemonModel).where(
            PokemonModel.national_pokedex_number == national_number
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def _require_by_national_number(self, national_number: int) -> PokemonModel:
        stmt = select(PokemonModel).where(
            PokemonModel.national_pokedex_number == national_number
        )
        return self.session.execute(stmt).scalar_one()

    def _upsert_pokemon_base(self, pokemon: Pokemon, image_path: str | None) -> None:
        stmt = sqlite_insert(PokemonModel).values(
            name=pokemon.name,
            national_pokedex_number=pokemon.national_number,
            category=pokemon.category,
            image_path=image_path,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[PokemonModel.national_pokedex_number],
            set_={
                "name": pokemon.name,
                "category": pokemon.category,
                "image_path": image_path,
            },
        )
        self.session.execute(stmt)

    def _upsert_stats(self, pokemon_id: int, pokemon: Pokemon) -> None:
        stmt = sqlite_insert(PokemonStatsModel).values(
            pokemon_id=pokemon_id,
            hp=pokemon.hp,
            attack=pokemon.attack,
            defense=pokemon.defense,
            special_attack=pokemon.special_attack,
            special_defense=pokemon.special_defense,
            speed=pokemon.speed,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[PokemonStatsModel.pokemon_id],
            set_={
                "hp": pokemon.hp,
                "attack": pokemon.attack,
                "defense": pokemon.defense,
                "special_attack": pokemon.special_attack,
                "special_defense": pokemon.special_defense,
                "speed": pokemon.speed,
            },
        )
        self.session.execute(stmt)

    def _upsert_evolution(self, pokemon_id: int, pokemon: Pokemon) -> None:
        stmt = sqlite_insert(PokemonEvolutionModel).values(
            pokemon_id=pokemon_id,
            prev_name=pokemon.evolutions.previous,
            next_name=pokemon.evolutions.next,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[PokemonEvolutionModel.pokemon_id],
            set_={
                "prev_name": pokemon.evolutions.previous,
                "next_name": pokemon.evolutions.next,
            },
        )
        self.session.execute(stmt)

    def _upsert_gender(self, pokemon_id: int, pokemon: Pokemon) -> None:
        if pokemon.gender is None:
            self.session.execute(
                delete(PokemonGenderModel).where(
                    PokemonGenderModel.pokemon_id == pokemon_id
                )
            )
            return

        stmt = sqlite_insert(PokemonGenderModel).values(
            pokemon_id=pokemon_id,
            male=pokemon.gender.male,
            female=pokemon.gender.female,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[PokemonGenderModel.pokemon_id],
            set_={
                "male": pokemon.gender.male,
                "female": pokemon.gender.female,
            },
        )
        self.session.execute(stmt)

    def _sync_types(self, pokemon_id: int, incoming_types: list[str]) -> None:
        incoming = self._normalize_strings(incoming_types)
        existing = self._load_existing_types(pokemon_id)

        self._insert_new_types(pokemon_id, incoming - existing)
        self._delete_missing_types(pokemon_id, existing - incoming)

    def _sync_abilities(self, pokemon_id: int, incoming_abilities: Iterable[Ability]) -> None:
        incoming_map = {
            ability.name.strip(): bool(ability.is_hidden)
            for ability in incoming_abilities
            if ability.name and ability.name.strip()
        }

        existing_names = self._load_existing_ability_names(pokemon_id)
        incoming_names = set(incoming_map.keys())

        self._upsert_ability_rows(pokemon_id, incoming_map)
        self._delete_missing_abilities(pokemon_id, existing_names - incoming_names)

    def _load_existing_types(self, pokemon_id: int) -> set[str]:
        rows = self.session.execute(
            select(PokemonTypeModel).where(PokemonTypeModel.pokemon_id == pokemon_id)
        ).scalars().all()
        return {row.type for row in rows}

    def _insert_new_types(self, pokemon_id: int, type_names: set[str]) -> None:
        for type_name in type_names:
            stmt = sqlite_insert(PokemonTypeModel).values(
                pokemon_id=pokemon_id,
                type=type_name,
            )
            stmt = stmt.on_conflict_do_nothing(
                index_elements=[PokemonTypeModel.pokemon_id, PokemonTypeModel.type]
            )
            self.session.execute(stmt)

    def _delete_missing_types(self, pokemon_id: int, type_names: set[str]) -> None:
        if not type_names:
            return

        self.session.execute(
            delete(PokemonTypeModel).where(
                PokemonTypeModel.pokemon_id == pokemon_id,
                PokemonTypeModel.type.in_(type_names),
            )
        )

    def _load_existing_ability_names(self, pokemon_id: int) -> set[str]:
        rows = self.session.execute(
            select(PokemonAbilityModel).where(PokemonAbilityModel.pokemon_id == pokemon_id)
        ).scalars().all()
        return {row.name for row in rows}

    def _upsert_ability_rows(self, pokemon_id: int, incoming_map: dict[str, bool]) -> None:
        for name, is_hidden in incoming_map.items():
            stmt = sqlite_insert(PokemonAbilityModel).values(
                pokemon_id=pokemon_id,
                name=name,
                is_hidden=is_hidden,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[PokemonAbilityModel.pokemon_id, PokemonAbilityModel.name],
                set_={"is_hidden": is_hidden},
            )
            self.session.execute(stmt)

    def _delete_missing_abilities(self, pokemon_id: int, ability_names: set[str]) -> None:
        if not ability_names:
            return

        self.session.execute(
            delete(PokemonAbilityModel).where(
                PokemonAbilityModel.pokemon_id == pokemon_id,
                PokemonAbilityModel.name.in_(ability_names),
            )
        )

    def _resolve_image_path_for_upsert(self, incoming: Pokemon) -> str | None:
        existing = self.get_by_national_number(incoming.national_number)

        if incoming.image_path is None:
            return existing.image_path if existing else None

        if not existing or not existing.image_path:
            return incoming.image_path

        if self._is_same_file_content(existing.image_path, incoming.image_path):
            return existing.image_path

        return incoming.image_path

    @staticmethod
    def _normalize_strings(values: Iterable[str]) -> set[str]:
        return {value.strip() for value in values if value and value.strip()}

    def _is_same_file_content(self, path_a: str, path_b: str) -> bool:
        file_a = Path(path_a)
        file_b = Path(path_b)

        if not file_a.exists() or not file_b.exists():
            return path_a == path_b

        return self._sha256(file_a) == self._sha256(file_b)

    @staticmethod
    def _sha256(file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
