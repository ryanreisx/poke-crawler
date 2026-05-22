from sqlalchemy.orm import Session
from app.database.connection import get_session
from app.database.repositories.pokemon_repository import PokemonRepository


class SqlAlchemyUnitOfWork:
    def __init__(self):
        self.session: Session | None = None

    def __enter__(self):
        self.session = get_session()
        self.pokemon_repository = PokemonRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self.session.close()