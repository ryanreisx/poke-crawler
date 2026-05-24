from __future__ import annotations

import asyncio
import httpx

from app.clients.bulbapedia_client import BulbapediaClient
from app.database.models.pokemon_model import PokemonModel
from app.database.unit_of_work import SqlAlchemyUnitOfWork
from app.exceptions.parsing_error import ParsingError
from app.models.pokemon import Pokemon
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

    async def close(self):
        await self.client.close()
        await self.image_service.close()

    async def crawl_and_persist(self, name: str) -> PokemonModel:
        pokemon = await self.crawl(name)

        with SqlAlchemyUnitOfWork() as uow:
            return uow.pokemon_repository.upsert(pokemon)

    async def crawl_and_persist_many(self, names: list[str], max_concurrency: int = 5) -> list[dict]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def worker(name: str) -> dict:
            async with semaphore:
                try:
                    persisted = await self.crawl_and_persist(name)
                    return {
                        "name": name,
                        "ok": True,
                        "national_number": persisted.national_pokedex_number,
                    }
                except Exception as exc:
                    return {
                        "name": name,
                        "ok": False,
                        "error": str(exc),
                        "error_type": self._classify_error(exc),
                    }

        tasks = [worker(name) for name in names]
        return await asyncio.gather(*tasks)

    async def crawl(self, name: str) -> Pokemon:
        html = await self.client.fetch_pokemon_page(name)
        pokemon = self.parser.parse(html)

        if pokemon.image_url:
            pokemon.image_path = await self.image_service.download(
                pokemon.image_url,
                f"{pokemon.name}.png",
            )

        return pokemon

    @staticmethod
    def _classify_error(exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            if exc.response.status_code == 404:
                return "not_found"
            return f"http_{exc.response.status_code}"

        if isinstance(exc, ParsingError):
            return "parsing_error"

        if isinstance(exc, httpx.HTTPError):
            return "network_error"

        return "unexpected_error"
