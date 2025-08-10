from typing import List
import psycopg2.extras

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import joinedload, sessionmaker

import src.models as Models

# Sentence transformers for comparsing 2 tags by cosine similarity
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
model = SentenceTransformer(model_name)
psycopg2.extras.register_uuid()


def insert_data_db():

    # Inizialisation of PostgreSQL DB
    POSTGRESQL_URL = "your_db"
    engine = create_engine(POSTGRESQL_URL)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    try:
        l = []
        superv_dict_list = []
        superv_name_list = []
        for j in supervisors:
            # Check if the supervisor exists
            if not j['name'] in superv_name_list:
                s4 = Models.GQW_supervisor(
                    name=j['name'], department=j['department'], degree=j['degree'])
                session.add(s4)
                session.commit()
                superv_name_list.append(j['name'])
        # Adding Graduate Qualification work
        for i in data:
            req_super = session.query(
                Models.GQW_supervisor.id, Models.GQW_supervisor.name).all()
            for n in req_super:
                if i['supervisor'] == n[1]:
                    s1 = Models.GQW_model(theme=i['theme'], type_of_qualification=i
                                          ['type_of_qualification'], abstract=i['abstract'], reference=i['reference'], supervisor_id=n[0])
                    session.add(s1)
                    session.commit()
                    for tag in i['tags'].split(','):
                        if not tag in l:
                            s2 = Models.GQW_tag(tag_name=tag, gqw_id=s1.id)
                            session.add(s2)
                            session.commit()
                            s3 = Models.GQW_vector(vector=str(np.array(
                                model.encode(tag)).reshape(1, -1)), tag_id=s2.id)
                            session.add(s3)
                            session.commit()
                            l.append(tag)
        print('The data is downloaded')
        result = session.query(Models.GQW_model).options(
            joinedload(Models.GQW_model.tag_gqw), joinedload(Models.GQW_model.supervisor_gqw)).all()
        return result
    except Exception as e:
        print(f'Something wrong: {e}')

    finally:
        # cur.close()
        session.close()


def build_filter(session, filter_dict: dict) -> List:
    """The filter for dynamic search throughout database

    Args:
        session (_type_): Database session (ex. POSTGRESql)
        filter_dict (dict): The dictationary of dynamic filters

    Returns:
        List: List of filters for the request
    """
    filters = []
    for key, value in filter_dict.items():
        if value:
            print(f'{key}: {value}')
            if isinstance(filter_dict[key], list):
                if key in ['theme', 'supervisor']:
                    filter_theme = []
                    filter_superv = []
                    for item in filter_dict[key]:
                        if key == 'theme':
                            filter_theme.append(
                                (Models.GQW_model.theme.icontains(item)))
                        else:
                            filter_superv.append(
                                getattr(Models.GQW_supervisor, 'name') == item)
                    filters.append(or_(*filter_theme))
                    filters.append(or_(*filter_superv))
                else:
                    filters.append(
                        getattr(Models.GQW_model, key).in_(filter_dict[key]))
            else:
                filters.append(getattr(Models.GQW_model, key) == value)
        else:
            pass
    return filters


if __name__ == '__main__':
    insert_data_db()

