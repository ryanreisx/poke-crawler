from app.parsers.pokemon_parser import PokemonParser


def load_fixture(name: str) -> str:
    with open(
        f"tests/fixtures/{name}",
        encoding="utf-8"
    ) as file:
        return file.read()


def test_parse_bulbasaur():
    html = load_fixture("bulbasaur.html")

    parser = PokemonParser()

    pokemon = parser.parse(html)

    assert pokemon.name == "Bulbasaur"

    assert pokemon.national_number == 1

    assert pokemon.category == "Seed Pokémon"

    assert pokemon.types == ["Grass", "Poison"]

    assert pokemon.hp == 45
    assert pokemon.attack == 49
    assert pokemon.defense == 49
    assert pokemon.special_attack == 65
    assert pokemon.special_defense == 65
    assert pokemon.speed == 45

    assert pokemon.evolutions.previous is None
    assert pokemon.evolutions.next == "Ivysaur"

    assert len(pokemon.abilities) > 0

    assert any(
        ability.name == "Overgrow"
        and ability.is_hidden is False
        for ability in pokemon.abilities
    )

    assert any(
        ability.name == "Chlorophyll"
        and ability.is_hidden is True
        for ability in pokemon.abilities
    )

    assert pokemon.image_path is not None

    assert pokemon.image_path.startswith("https://")

    assert ".png" in pokemon.image_path


