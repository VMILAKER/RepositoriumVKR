from functools import lru_cache
from typing import List

import os
import re
import shutil
import numpy as np
from fastapi import HTTPException
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import and_, select

import src.models as Models
from utilities import build_filter


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
        model_name = 'Alibaba-NLP/gte-multilingual-base'
        model = SentenceTransformer(model_name)

        filter_dict = {
            'id': [],
        }

        if not filter_dict.values():
            return 'No findings'
        else:
            if qualification_:
                filter_dict['type_of_qualification'] = qualification_
            if theme_:
                filter_dict['theme'] = [str(i.strip())
                                        for i in theme_.split(',') if i]
            if supervisor_:
                filter_dict['supervisor'] = [str(i.strip())
                                             for i in supervisor_.split(',') if i]
            elif tags_:
                tags_list = [i.strip().lower() for i in tags_.split(',')] 
                for tag in tags_list:
                    similarity_dict = {}
                    common_similarity = 0
                    result = db.query(Models.Middle.vkr_id, Models.GQW_vector.vector).filter(
                        Models.Middle.tags_id == Models.GQW_vector.tag_id).all()
                    embedding = np.array(model.encode(tag)).reshape(1, -1)
                    for i in range(len(result)):
                        tags_db = np.array(result[i][1].replace('[', '').replace(']', '').replace('\n', '').split()).reshape(1,-1)
                        # print(tags_db)
                        similarity = float(
                            f'{cosine_similarity(embedding, tags_db)[0][0]:.2f}')
                        common_similarity += similarity
                        c = similarity_dict.setdefault(
                            result[i][0], similarity)
                    for key in similarity_dict.keys():
                        # if (similarity_dict[key] >= (common_similarity / len(result))):
                        if (similarity_dict[key] >= 0.6):
                            if not key in filter_dict['id']:
                                filter_dict['id'].append(key)
                    print(tag, similarity_dict)
                if not filter_dict['id']:
                    return "No findings by tag's query"
            if db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).join(Models.GQW_model.type_of_qualification).filter(and_(*build_filter(db, filter_dict))).all():
                return db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).join(Models.GQW_model.type_of_qualification).filter(and_(*build_filter(db, filter_dict))).order_by(Models.GQW_model.type_of_qualification).all()
            else:
                return 'Nothing to say'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')


def upload_gqw_data_sql(data: dict, db):
    model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    model = SentenceTransformer(model_name)
    # print(dict(data))
    # data = dict(data)
    # for key in data.keys():
    #     data[key] = re.sub(r"\s+", "", data[key])
    try:
        if not db.query(Models.GQW_model).filter(Models.GQW_model.theme == data.theme).count():
            if not db.query(Models.GQW_qualification).filter(Models.GQW_qualification.qualification == data.type_of_qualification).count():
                s7 = Models.GQW_qualification(qualification=data.type_of_qualification)
                db.add(s7)
                db.commit()
            if not db.query(Models.Supervisor_department).filter(Models.Supervisor_department.department == data.department).count():
                s5 = Models.Supervisor_department(department=data.department)
                db.add(s5)
                db.commit()
            if not db.query(Models.Supervisor_degree).filter(Models.Supervisor_degree.degree == data.degree).count():
                s6 = Models.Supervisor_degree(degree=data.degree)
                db.add(s6)
                db.commit()
            if not db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).count():
                dep = db.query(Models.Supervisor_department).filter(Models.Supervisor_department.department == data.department).one()
                deg = db.query(Models.Supervisor_degree).filter(Models.Supervisor_degree.degree == data.degree).one()

                s4 = Models.GQW_supervisor(
                    name=data.supervisor, department_id=dep.id, degree_id=deg.id)
                db.add(s4)
                db.commit()
            if db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).count():
                n = db.query(Models.GQW_supervisor).filter(
                    Models.GQW_supervisor.name == data.supervisor).one()
                qualific_request = db.query(Models.GQW_qualification).filter(Models.GQW_qualification.qualification == data.type_of_qualification).one()
                print(qualific_request)
                s1 = Models.GQW_model(theme=data.theme, qualification_id=qualific_request.id,
                                      abstract=data.abstract, reference=data.reference, supervisor_id=n.id)
                db.add(s1)
                db.commit()

            for tag in data.tags.split(','):
                if not db.query(Models.GQW_tag).filter(Models.GQW_tag.tag_name == tag).count():
                    s2 = Models.GQW_tag(tag_name=str(tag).strip())
                    db.add(s2)
                    db.commit()
                    sm = Models.Middle(vkr_id=s1.id, tags_id=s2.id)
                    db.add(sm)
                    s3 = Models.GQW_vector(vector=
                        str(np.array(model.encode(tag.lower())).reshape(1, -1)), tag_id=s2.id)
                    db.add(s3)
                    db.commit()
                else:
                    tags = db.query(Models.GQW_tag).filter(Models.GQW_tag.tag_name == tag).one()
                    sm = Models.Middle(vkr_id=s1.id, tags_id=tags.id)
                    db.add(sm)
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
            filepath = r'/Backend/app'
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
