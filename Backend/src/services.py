# from functools import lru_cache
from typing import List

import os
import re
import shutil
import datetime
from datetime import timedelta
import numpy as np
import uuid
from fastapi import HTTPException
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import and_, update

from pdfminer.high_level import extract_text
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, TA_CENTER, TA_JUSTIFY, TA_LEFT, ParagraphStyle
import shutil
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
# from sqlalchemy.orm import distinct

import src.models as Models
from utilities import build_filter
import src.dto as DTO

styles = getSampleStyleSheet()
styles['Normal'].fontName = 'TNR'
pdfmetrics.registerFont(TTFont('TNR', 'TNR.ttf', 'UTF-8'))

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
                        if (similarity_dict[key] >= 0.7):
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
                s1 = Models.GQW_model(theme=data.theme, qualification_id=qualific_request.id, reference=data.reference, supervisor_id=n.id)
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


def upload_file(file, db):

    justify_style = ParagraphStyle(
        name="JustifiedStyle", parent=styles["Normal"], alignment=TA_JUSTIFY, leading=24, spaceAfter=24, firstLineIndent=25, fontSize=14)
    center_style = ParagraphStyle(
        name="CenteredStyle", parent=styles["Normal"], alignment=TA_CENTER, spaceAfter=10, fontSize=16)
    left_style = ParagraphStyle(
        name="CenteredStyle", parent=styles["Normal"], alignment=TA_LEFT, fontSize=12)
    try:
        if (file.filename).endswith('.pdf'):
            filepath_full = r'/Backend/app/full_pdf'
            filepath_compressed = r'/Backend/app'
            contents = file.file
            with open(os.path.join(filepath_full, file.filename), 'wb') as buffer:
                shutil.copyfileobj(contents, buffer)
            list_word = ['аннотация',
                         'annotation', 'abstract']
            header_template = 'оглавление'
            text_merge = [extract_text(contents, page_numbers=[i]) for i in range(8) for w in list_word if
                          w in extract_text(contents, page_numbers=[i]).lower()]

            # header = [extract_text(contents, page_numbers=[i, i+1]) for i in range(3, 11) if
            #           header_template in extract_text(contents, page_numbers=[i]).lower()]

            # pattern = r'(\\d+\\.{1,})\\s+([\\w\\s]+)\\s*\\.{1,}\\s*(\\d+)'

            # header = (' '.join(header)).replace('_', '').replace('\x0c', '')
            # result = re.findall(pattern, header)
            # print(result)
            # header = [re.sub(pattern, replace, i).strip() for i in re.split(
            #     r'(ОГЛАВЛЕНИЕ|Оглавление|Введение{1}|ВВЕДЕНИЕ{1})', header) if i]

            text = (' '.join(text_merge)).replace(
                '\n', ' ').replace('_', '').replace('\x0c', '')
            text = [re.sub(r'^\\W\\d]*\\d+$', '', i).strip() for i in re.split(
                r'(Аннотация|АННОТАЦИЯ|ABSTRACT|Annotation)', text) if i]

            if text[0].lower() not in list_word:
                text.pop(0)
            if text[1][-1] is int:
                text[1] = text[1][-1]
            if db.query(Models.GQW_model).filter(Models.GQW_model.reference== file.filename).count():       
                s1 = db.query(Models.GQW_model).filter(Models.GQW_model.reference== str(file.filename)).update({'abstract': f'{text[1]}'})
                # db.session.add(s1)
                db.commit()
                print('OK')
            # print(repr(text))
            # print(header)
            doc = SimpleDocTemplate(os.path.join(filepath_compressed, file.filename), pagesize=A4)
            p1 = Paragraph(str(text[0]).replace(
                "\n", "<br />"), center_style)

            p2 = Paragraph(str(text[1]).replace(
                "\n", "<br />"), justify_style)

            p3 = Paragraph(str(text[2]).replace(
                "\n", "<br />"), center_style)
            p4 = Paragraph(str(text[3][:-1]).replace(
                "\n", "<br />"), justify_style)

            # p5 = Paragraph(str(header[0]).replace(
            #     "\n", "<br />"), center_style)
            # p6 = Paragraph(str(header[1][:-1]).replace(
            #     "\n", "<br />"), left_style)
            doc.build([p1, p2, p3, p4],)
            return 'The file is uploaded'
        else:
            return 'Please, attach .pdf file'
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Something went wrong: {e}')
    finally:
        file.file.close()


def post_passkey(passkey: DTO.PassKey, db):
    try:
        gqw_id_converted = uuid.UUID(passkey.gqw_id)
        if not db.query(Models.Visitor).filter(Models.Visitor.visitor_id == passkey.visitor_id).count():
            s1 = Models.Visitor(visitor_id = passkey.visitor_id)
            db.add(s1)
            db.commit()
        if not db.query(Models.PassKeys).filter(and_(Models.PassKeys.token_encoded == passkey.password, Models.PassKeys.gqw_id == gqw_id_converted, Models.PassKeys.visitor_f == passkey.visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())).count():
            s2 = Models.PassKeys(token_encoded = passkey.password, date_of_get=datetime.datetime.now(), date_expired=(datetime.datetime.now() + timedelta(days=1)), visitor_f= passkey.visitor_id, gqw_id= gqw_id_converted)
            db.add(s2)
            db.commit()
            return 'Data is uploaded'
        else:
            return 'Password is already created and valid'
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Something went wrong: {e}')
    finally:
        db.close()


def get_passkey(password: str, gqw_id: str, visitor_id, db):
    try:
        if visitor_id and db.query(Models.PassKeys).join(Models.Visitor).filter(and_(Models.PassKeys.visitor_f == visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())).count():
            return [{'id': f'{item.gqw_id}'} for item in db.query(Models.PassKeys.gqw_id).join(Models.Visitor).filter(and_(Models.PassKeys.visitor_f == visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())).distinct()]
        if gqw_id:
            gqw_id_converted = uuid.UUID(gqw_id)
            if db.query(Models.PassKeys).join(Models.Visitor).filter(and_(Models.PassKeys.gqw_id == gqw_id_converted,  Models.PassKeys.token_encoded == password, Models.PassKeys.date_expired >= datetime.datetime.now())).count():
                return [{'id': f'{item.gqw_id}'} for item in db.query(Models.PassKeys.gqw_id).join(Models.Visitor).filter(and_(Models.PassKeys.gqw_id == gqw_id_converted,  Models.PassKeys.token_encoded == password, Models.PassKeys.date_expired >= datetime.datetime.now())).distinct()]
            else:
                return 'Unvalid key'
        else:
            return 'No data'
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Something went wrong: {e}')
    finally:
        db.close()


def get_preloaded_data(db):
    try:
        if db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).join(Models.GQW_model.type_of_qualification).all():
            return [[item.theme for item in db.query(Models.GQW_model.theme).distinct() if item.theme], [item.reference for item in db.query(Models.GQW_model.reference).distinct() if item.reference], [{'value':item.department, 'label':item.department} for item in db.query(Models.Supervisor_department.department).distinct() if item.department], [{'value':item.name, 'label':item.name} for item in db.query(Models.GQW_supervisor.name).distinct() if item.name], [{'value':item.degree, 'label':item.degree} for item in db.query(Models.Supervisor_degree.degree).distinct() if item.degree], [{'value':item.tag_name, 'label':item.tag_name} for item in db.query(Models.GQW_tag.tag_name).distinct() if item.tag_name]]
        else:
            return 'No data'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()