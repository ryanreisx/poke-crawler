import asyncio

from app.clients.bulbapedia_client import BulbapediaClient
from app.parsers.pokemon_parser import PokemonParser



async def main():
    client = BulbapediaClient()
    parser = PokemonParser()

    html = await client.fetch_pokemon_page("Pikachu")
    pokemon = parser.parse(html)


asyncio.run(main())