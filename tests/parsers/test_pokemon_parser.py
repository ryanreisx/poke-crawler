import pytest
from bs4 import BeautifulSoup

from app.exceptions.parsing_error import ParsingError
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

    assert pokemon.image_url is not None

    assert pokemon.image_url.startswith("https://")

    assert ".png" in pokemon.image_url


def test_parse_raises_when_infobox_is_missing():
    parser = PokemonParser()
    html = "<html><body><h1>Bulbasaur</h1></body></html>"

    with pytest.raises(ParsingError, match="Pokemon infobox not found"):
        parser.parse(html)


def test_parse_national_number_raises_on_invalid_format():
    parser = PokemonParser()
    infobox_html = """
    <table class="roundy infobox">
      <tr>
        <td><a title="List of Pokémon by National Pokédex number">No. ???</a></td>
      </tr>
    </table>
    """
    infobox = BeautifulSoup(infobox_html, "lxml").find("table")

    with pytest.raises(ParsingError, match="Invalid national number format"):
        parser.parse_national_number(infobox)


def test_parse_category_raises_when_category_link_is_missing():
    parser = PokemonParser()
    infobox_html = """
    <table class="roundy infobox">
      <tr><td>Without category link</td></tr>
    </table>
    """
    infobox = BeautifulSoup(infobox_html, "lxml").find("table")

    with pytest.raises(ParsingError, match="Pokemon category not found"):
        parser.parse_category(infobox)


def test_parse_base_stats_raises_when_stats_are_incomplete():
    parser = PokemonParser()
    html = """
    <html><body>
      <table>
        <tr><th><a>HP</a><div></div><div>45</div></th></tr>
        <tr><th><a>Attack</a><div></div><div>49</div></th></tr>
      </table>
    </body></html>
    """
    soup = BeautifulSoup(html, "lxml")

    with pytest.raises(ParsingError, match="Missing base stats"):
        parser.parse_base_stats(soup)


