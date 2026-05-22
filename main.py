import asyncio

from app.database.connection import init_db
from app.services.pokemon_service import PokemonService


async def main():
    init_db()

    service = PokemonService()
    persisted = await service.crawl_and_persist("Magikarp")


asyncio.run(main())