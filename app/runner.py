from app.database.connection import init_db
from app.services.pokemon_service import PokemonService


async def run_crawler(pokemon_names: list[str]) -> list[dict[str, object]]:
    init_db()

    service = PokemonService()
    return await service.crawl_and_persist_many(pokemon_names)
