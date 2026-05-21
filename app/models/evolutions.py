from pydantic import BaseModel

class Evolutions(BaseModel):
    previous: str | None = None
    next: str | None = None