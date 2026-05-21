from pydantic import BaseModel
from .evolutions import Evolutions
from .ability import Ability

class Pokemon(BaseModel):
    name: str
    national_number: int
    category: str
    types: list[str]
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    evolutions: Evolutions
    abilities: list[Ability]
    image_path: str