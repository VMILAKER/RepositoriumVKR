from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

POSTGRESQL_URL = "your_db_url"

engine = create_engine(POSTGRESQL_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db_nosql():
    client = MongoClient(host='mongodb://localhost:27017/')
    try:
        db = client['vkr_client']
        collection = db['vkr']
        yield collection
    finally:
        client.close()


def get_db_sql():
    """Launch POSTGRESql database session 

    Yields:
        _type_: Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

