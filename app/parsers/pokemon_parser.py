import re
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup, Tag

from app.models.ability import Ability
from app.models.evolutions import Evolutions
from app.models.pokemon import Pokemon
from app.models.pokemon import Gender
from app.exceptions.parsing_error import ParsingError


class PokemonParser:
    BASE_URL = "https://bulbapedia.bulbagarden.net"

    def parse(self, html: str) -> Pokemon:
        soup = BeautifulSoup(html, "lxml")
        infobox = self.parse_infobox(soup)
        gender = self.parse_gender(infobox)

        name = self.parse_name(soup)
        national_number = self.parse_national_number(infobox)
        category = self.parse_category(infobox)
        types = self.parse_types(infobox)
        stats = self.parse_base_stats(soup)
        evolutions = self.parse_evolutions(soup, name)
        abilities = self.parse_abilities(infobox)
        image_url = self.parse_image_url(infobox)

        return Pokemon(
            name=name,
            national_number=national_number,
            category=category,
            types=types,
            hp=stats["hp"],
            attack=stats["attack"],
            defense=stats["defense"],
            special_attack=stats["special_attack"],
            special_defense=stats["special_defense"],
            speed=stats["speed"],
            evolutions=evolutions,
            abilities=abilities,
            image_url=image_url,
            gender = gender
        )

    def parse_infobox(self, soup: BeautifulSoup) -> Tag:
        infobox = soup.find("table", class_="roundy infobox")

        if not infobox:
            raise ParsingError("Pokemon infobox not found")
        
        return infobox

    def parse_name(self, soup: BeautifulSoup) -> str:
        title = soup.find("h1")
        if not title:
            raise ParsingError("Pokemon name not found")
        
        return self._clean_name(title.get_text(strip=True))

    def parse_national_number(self, infobox: Tag) -> int:
        number_link = infobox.find(
            "a",
            title="List of Pokémon by National Pokédex number",
        )

        if not number_link:
            raise ParsingError("National number link not found")

        text = number_link.get_text(strip=True)
        digits = "".join(char for char in text if char.isdigit())

        if not digits:
            raise ParsingError("Invalid national number format")
        
        return int(digits)

    def parse_category(self, infobox: Tag) -> str:
        category_link = infobox.find("a", title="Pokémon category")

        if not category_link:
            raise ParsingError("Pokemon category not found")
        
        return category_link.get_text(" ", strip=True)

    def parse_types(self, infobox: Tag) -> list[str]:
        type_section = infobox.find("a", title="Type")

        if not type_section:
            raise ParsingError("Type section not found")

        type_container = type_section.find_parent("td")

        if not type_container:
            raise ParsingError("Type container not found")

        types: list[str] = []
        for link in type_container.find_all("a", title=lambda v: bool(v and v.endswith("(type)"))):
            parent_td = link.find_parent("td")

            if parent_td and self._is_hidden_by_style(parent_td):
                continue

            type_name = link.get_text(strip=True)
            if not type_name or type_name == "Unknown":
                continue

            if type_name not in types:
                types.append(type_name)
        
        if not types:
          raise ParsingError("No types found")

        return types

    def parse_base_stats(self, soup: BeautifulSoup) -> dict[str, int]:
        stat_mapping = {
            "HP": "hp",
            "Attack": "attack",
            "Defense": "defense",
            "Sp. Atk": "special_attack",
            "Sp. Def": "special_defense",
            "Speed": "speed",
        }

        stats: dict[str, int] = {}
        for row in soup.find_all("tr"):
            th = row.find("th")
            if not th:
                continue

            stat_link = th.find("a")
            if not stat_link:
                continue

            stat_name = stat_link.get_text(strip=True)
            if stat_name not in stat_mapping:
                continue

            value_divs = th.find_all("div", recursive=False)
            if len(value_divs) < 2:
                continue

            raw_value = value_divs[1].get_text(strip=True)
            if raw_value.isdigit():
                stats[stat_mapping[stat_name]] = int(raw_value)

        missing = [v for v in stat_mapping.values() if v not in stats]
        if missing:
            raise ParsingError(f"Missing base stats: {', '.join(missing)}")

        return stats

    def parse_evolutions(self, soup: BeautifulSoup, current_name: str) -> Evolutions:
        evo_span = soup.find("span", id="Evolution")
        if not evo_span:
            return Evolutions(previous=None, next=None)

        heading = evo_span.find_parent(["h2", "h3", "h4"])
        if not heading:
            raise ParsingError("Evolution section found but heading structure changed")

        table = heading.find_next("table")
        if not table:
            raise ParsingError("Evolution section found but table not found")

        names: list[str] = []
        for a in table.find_all("a", href=True):
            parsed_name = self._name_from_href(a["href"])
            if parsed_name:
                names.append(parsed_name)

        names = list(dict.fromkeys(names))
        if not names:
            raise ParsingError("Evolution section found but no names extracted")

        cur = self._norm(current_name)
        idx = next((i for i, n in enumerate(names) if self._norm(n) == cur), None)
        if idx is None:
            return Evolutions(previous=None, next=None)  

        previous = names[idx - 1] if idx > 0 else None
        next_ = names[idx + 1] if idx + 1 < len(names) else None
        return Evolutions(previous=previous, next=next_)

    def parse_abilities(self, infobox: Tag) -> list[Ability]:
        section_td = None
        for td in infobox.find_all("td"):
            if td.find("a", href="/wiki/Ability"):
                section_td = td
                break

        if not section_td:
            raise ParsingError("Abilities section not found")

        inner_table = section_td.find("table", class_="roundy")
        if not inner_table:
            raise ParsingError("Abilities table not found")

        abilities: list[Ability] = []
        seen: set[str] = set()

        for cell in inner_table.find_all("td"):
            if self._is_hidden_by_style(cell):
                continue

            link = cell.find("a", href=True)
            if not link:
                continue

            href = link["href"]
            if not href.endswith("_(Ability)"):
                continue

            name = link.get_text(strip=True)
            if not name:
                continue

            small_text = " ".join(
                s.get_text(" ", strip=True) for s in cell.find_all("small")
            ).lower()
            is_hidden = "hidden ability" in small_text

            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)

            abilities.append(Ability(name=name, is_hidden=is_hidden))

        if not abilities:
            raise ParsingError("No abilities found")
        
        return abilities

    def parse_image_url(self, infobox: Tag) -> str | None:
        img = infobox.find("img")
        if img and img.get("src"):
            return urljoin(self.BASE_URL, img["src"])

        file_link = infobox.find("a", href=lambda h: isinstance(h, str) and h.startswith("/wiki/File:"))
        if file_link and file_link.get("href"):
            return urljoin(self.BASE_URL, file_link["href"])

        return None

    def _clean_name(self, name: str) -> str:
        return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()

    def _norm(self, value: str) -> str:
        value = value.replace("♂", "").replace("♀", "")
        return re.sub(r"\s+", " ", value).strip().casefold()

    def _name_from_href(self, href: str) -> str | None:
        if not href or not href.startswith("/wiki/"):
            return None

        raw = unquote(href[len("/wiki/"):])

        if raw.startswith("File:"):
            filename = raw[len("File:"):].split("/")[-1].split("?")[0]
            if not filename.lower().endswith(".png"):
                return None

            stem = filename[:-4]
            stem = re.sub(r"^Menu_HOME_\d+_?", "", stem)
            stem = re.sub(r"^\d+", "", stem)
            stem = stem.replace("_", " ").strip()
            return stem or None

        if "(type)" in raw:
            return None

        match = re.match(r"^(.*?)_\(Pok.*?\)$", raw)
        if match:
            return match.group(1).replace("_", " ").strip()

        return None

    def _is_hidden_by_style(self, node: Tag) -> bool:
        style = (node.get("style") or "").replace(" ", "").lower()

        return "display:none" in style
    

    def parse_gender(self, infobox: Tag) -> Gender | None:
        link = infobox.find("a", title="List of Pokémon by gender ratio")
        if not link:
            return None

        parent_td = link.find_parent("td")
        if not parent_td:
            raise ParsingError("Gender section found but parent container not found")

        inner_table = parent_td.find("table")
        if not inner_table:
            raise ParsingError("Gender section found but table not found")

        visible_tds = []
        for td in inner_table.find_all("td"):
            if not self._is_hidden_by_style(td):
                visible_tds.append(td)

        if not visible_tds:
            raise ParsingError("Gender section found but no visible data")

        male = 0.0
        female = 0.0

        for span in visible_tds[-1].find_all("span"):
            text = span.get_text(strip=True)
            if "female" in text:
                parts = text.split("%")
                female = float(parts[0])
            elif "male" in text:
                parts = text.split("%")
                male = float(parts[0])

        if male == 0.0 and female == 0.0:
            return None

        return Gender(male=male, female=female)

