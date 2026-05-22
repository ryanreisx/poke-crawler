import asyncio

from app.clients.bulbapedia_client import BulbapediaClient
from app.database.connection import get_session, init_db
from app.database.repositories.pokemon_repository import PokemonRepository
from app.parsers.pokemon_parser import PokemonParser
from app.services.image_service import ImageService


async def main():
    client = BulbapediaClient()
    parser = PokemonParser()
    image_service = ImageService()

    html = await client.fetch_pokemon_page("Pikachu")
    pokemon = parser.parse(html)
    image_path = await image_service.download(pokemon.image_url, f"{pokemon.name}.png")

    pokemon.image_path = image_path

    init_db()

    session = get_session()
    try:
        pokemon_repository = PokemonRepository(session)
        persisted = pokemon_repository.upsert(pokemon)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

asyncio.run(main())