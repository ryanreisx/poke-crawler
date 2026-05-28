from pydantic import BaseModel

class Gender(BaseModel):
    male: float
    female: float