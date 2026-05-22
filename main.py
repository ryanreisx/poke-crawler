import asyncio

from app.runner import run_crawler


def main() -> None:
    pokemons = ["Crobat", "Garchomp", "Greninja", "Lucario", "Mimikyu", "Scizor", "Talonflame"]

    asyncio.run(run_crawler(pokemons))



if __name__ == "__main__":
    main()