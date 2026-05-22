from __future__ import annotations

from typing import Callable

from app.clients.bulbapedia_client import BulbapediaClient
from app.database.models.pokemon_model import PokemonModel
from app.database.unit_of_work import SqlAlchemyUnitOfWork
from app.parsers.pokemon_parser import PokemonParser
from app.services.image_service import ImageService


class PokemonService:
    def __init__(
        self,
        client: BulbapediaClient | None = None,
        parser: PokemonParser | None = None,
        image_service: ImageService | None = None,
    ):
        self.client = client or BulbapediaClient()
        self.parser = parser or PokemonParser()
        self.image_service = image_service or ImageService()

    async def crawl_and_persist(self, name):
        pokemon = await self.crawl(name)

        with SqlAlchemyUnitOfWork() as uow:
            return uow.pokemon_repository.upsert(pokemon)
        
    
    async def crawl(self, name) -> PokemonModel:
        html = await self.client.fetch_pokemon_page(name)
        pokemon = self.parser.parse(html)

        if pokemon.image_url:
            pokemon.image_path = await self.image_service.download(
                pokemon.image_url,
                f"{pokemon.name}.png",
            )

        return pokemon
