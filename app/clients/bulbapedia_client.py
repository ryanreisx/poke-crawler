import httpx

class BulbapediaClient:
    BASE_URL = "https://bulbapedia.bulbagarden.net/wiki"

    async def fetch_pokemon_page(self, name: str) -> str:
        pokemon_name = name.replace(" ", "_")

        url = f"{self.BASE_URL}/{pokemon_name}_(Pokémon)"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)

            response.raise_for_status()

            return response.text
