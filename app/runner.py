from app.database.connection import init_db
from app.services.pokemon_service import PokemonService


async def run_crawler(pokemon_names: list[str]) -> None:
    init_db()

    service = PokemonService()

    for name in pokemon_names:
        await service.crawl_and_persist(name)