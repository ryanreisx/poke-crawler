from os import name

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

class BulbapediaClient:
    BASE_URL = "https://bulbapedia.bulbagarden.net/wiki"

    @staticmethod
    def _should_retry(exc: Exception) -> bool:
        if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            return status == 429 or 500 <= status < 600
        return False

    @retry(
        retry=retry_if_exception(_should_retry),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def fetch_pokemon_page(self, name: str) -> str:
        pokemon_name = " ".join(name.strip().split())

        if pokemon_name.isupper():
            pokemon_name = pokemon_name.capitalize()

        pokemon_name =  pokemon_name.replace(" ", "_")

        url = f"{self.BASE_URL}/{pokemon_name}_(Pokémon)"

        async with httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "pokemon-crawler/1.0"},
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
