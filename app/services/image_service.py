import os
import httpx
from pathlib import Path
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_DIR = BASE_DIR / "data" / "images"

class ImageService:
    def __init__(self, base_path: str | Path | None = None):
        self.base_path = Path(base_path) if base_path else IMAGE_DIR
        os.makedirs(self.base_path, exist_ok=True)
        self._client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self._client.aclose()

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def download(self, url: str, filename: str) -> str:
        response = await self._client.get(url)
        response.raise_for_status()

        file_path = self.base_path / filename
        file_path.write_bytes(response.content)

        return str(file_path.relative_to(BASE_DIR).as_posix())
