from pydantic import BaseModel

class Ability(BaseModel):
    name: str
    is_hidden: bool