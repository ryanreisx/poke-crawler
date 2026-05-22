import asyncio
import logging
import sys

from app.logging_config import configure_logging
from app.runner import run_crawler


def main() -> None:
    configure_logging()

    pokemon_names = [name.strip() for name in sys.argv[1:] if name.strip()]

    if not pokemon_names:
        logging.error("Usage: python main.py <pokemon1> <pokemon2> ...")
        raise SystemExit(1)

    asyncio.run(run_crawler(pokemon_names))

if __name__ == "__main__":
    main()
