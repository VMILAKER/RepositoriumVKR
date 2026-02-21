from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

POSTGRESQL_URL = "postgresql://login:password@postgres-repositorium/database"

engine = create_engine(POSTGRESQL_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db_sql():
    """Launch POSTGRESql database session 

    Yields:
        _type_: Session
    """

    db = SessionLocal()
    db.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    try:
        yield db
    finally:
        db.close()

