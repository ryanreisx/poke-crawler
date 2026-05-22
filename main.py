import asyncio
import sys

from app.runner import run_crawler


def main() -> None:
    pokemon_names = [name.strip() for name in sys.argv[1:] if name.strip()]

    if not pokemon_names:
        print("Usage: python main.py <pokemon1> <pokemon2> ...", file=sys.stderr)
        raise SystemExit(1)

    asyncio.run(run_crawler(pokemon_names))

if __name__ == "__main__":
    main()
