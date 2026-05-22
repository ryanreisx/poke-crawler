import logging

from app.database.connection import init_db
from app.services.pokemon_service import PokemonService


logger = logging.getLogger(__name__)


async def run_crawler(pokemon_names: list[str]) -> list[dict[str, object]]:
    init_db()

    service = PokemonService()
    results = await service.crawl_and_persist_many(pokemon_names)

    for result in results:
        if not result["ok"]:
            logger.error(
                "Pokemon failed | name=%s error_type=%s",
                result["name"],
                result["error_type"],
            )

    return results
