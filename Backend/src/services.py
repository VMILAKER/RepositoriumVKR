from functools import lru_cache
from typing import List
import shutil
import os
import numpy as np
from fastapi import HTTPException
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import and_

import src.models as Models
from utilities import build_filter


@lru_cache
def get_vkr(theme: str, supervisor: str, type_of_qualification: str, abstract: str, tags: List[str], client):
    try:
        return client.find({"Theme": theme, "Supervisor": supervisor, "Type_of_qualification": type_of_qualification, "Abstract": abstract, "Tags": tags, "_id": 0})
    except Exception as e:
        HTTPException(status_code='404', detail=f'The error is: {e}')


@lru_cache(maxsize=None)
def get_gqw_data_sql(theme_: str, supervisor_: str, qualification_: str, tags_: str, db):
    """Extracting data from POSTGRESQL by certain parametrs.
    P.S. GQW- Graduate Qualification work

    Args:
        theme (str): the potential theme, which should be got
        supervisor (str): the supervisor of certain GQW
        qualification (str): requested qualification of GQW
        tags (str): tags to ease GQW's search
        db (_type_): Database session (ex. POSTGRESql)

    Returns:
        List[dict]: the dictationary or list of dictationaries with the requsted data
    """
    try:
        model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        model = SentenceTransformer(model_name)

        filter_dict = {
            'id': [],
            'type_of_qualification': qualification_
        }

        if not filter_dict.values():
            return 'No findings'
        else:
            if theme_:
                filter_dict['theme'] = [str(i.strip())
                                        for i in theme_.split(',') if i]
            if supervisor_:
                filter_dict['supervisor'] = [str(i.strip())
                                             for i in supervisor_.split(',') if i]
            elif tags_:
                tags_list = [i.strip() for i in tags_.split(',')]
                for tag in tags_list:
                    common_similarity = 0
                    similarity_dict = {}
                    result = db.query(Models.GQW_tag.gqw_id, Models.GQW_vector.vector).filter(
                        Models.GQW_tag.id == Models.GQW_vector.tag_id).all()
                    embedding = np.array(model.encode(tag)).reshape(1, -1)
                    for i in range(len(result)):
                        tags_db = np.array(result[i][1].replace(
                            '[', '').replace(']', '').replace('\n', '').split()).reshape(1, -1)
                        similarity = float(
                            f'{cosine_similarity(embedding, tags_db)[0][0]:.2f}')
                        common_similarity += similarity
                        c = similarity_dict.setdefault(
                            result[i][0], similarity)
                    for key in similarity_dict.keys():
                        if similarity_dict[key] >= (common_similarity / len(result)):
                            if not key in filter_dict['id']:
                                filter_dict['id'].append(key)
                if not filter_dict['id']:
                    return "No findings by tag's query"
            if db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).filter(and_(*build_filter(db, filter_dict))).all():
                return db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).filter(and_(*build_filter(db, filter_dict))).all()
            else:
                return 'Nothing to say'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')


def upload_gqw_data_sql(data, db):
    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    model = SentenceTransformer(model_name)

    try:
        # req_sup_name = db.query(Models.GQW_supervisor.name).all()
        if not db.query(Models.GQW_model).filter(Models.GQW_model.theme == data.theme).count():
            s1 = ''
            if not db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).count():
                print(data.supervisor)
                s4 = Models.GQW_supervisor(
                    name=data.supervisor, department=data.department, degree=data.degree)
                db.add(s4)
                db.commit()
                s1 = Models.GQW_model(theme=data.theme, type_of_qualification=data.type_of_qualification,
                                      abstract=data.abstract, reference=data.reference, supervisor_id=s4.id)
                db.add(s1)
                db.commit()
            else:
                n = db.query(Models.GQW_supervisor).filter(
                    Models.GQW_supervisor.name == data.supervisor).one()
                print(n.name)
                s1 = Models.GQW_model(theme=data.theme, type_of_qualification=data.type_of_qualification,
                                      abstract=data.abstract, reference=data.reference, supervisor_id=n.id)
                db.add(s1)
                db.commit()

            for tag in data.tags.split(','):
                if not db.query(Models.GQW_tag).filter(Models.GQW_tag.tag_name == tag).count():
                    s2 = Models.GQW_tag(tag_name=tag, gqw_id=s1.id)
                    db.add(s2)
                    db.commit()
                    s3 = Models.GQW_vector(vector=str(np.array(
                        model.encode(tag)).reshape(1, -1)), tag_id=s2.id)
                    db.add(s3)
                    db.commit()
            return 'The data is downloaded'
        else:
            return f'{data.theme} already exists'
    except Exception as e:
        print(f'Something wrong: {e}')
    finally:
        db.close()


def upload_file(file):
    try:
        if (file.filename).endswith('.pdf'):
            filepath = r'C:\Users\Sofi\OneDrive\Desktop\Repositorium\Frontend\vite-project\public\pdf_docs'
            contents = file.file
            print(str(contents))
            with open(os.path.join(filepath, file.filename), 'wb') as buffer:
                shutil.copyfileobj(contents, buffer)
            return 'The file is uploaded'
        else:
            return 'Please, attach .pdf file'
    except Exception:
        raise HTTPException(status_code=500, detail='Something went wrong')
    finally:
        file.file.close()
