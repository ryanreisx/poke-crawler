import asyncio

from app.clients.bulbapedia_client import BulbapediaClient
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

    print(pokemon)


asyncio.run(main())