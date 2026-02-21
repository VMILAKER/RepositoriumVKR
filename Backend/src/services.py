import datetime
import os
import random
import re
import shutil
import uuid
from datetime import timedelta

import requests
from fastapi import HTTPException
from pdfminer.high_level import extract_text
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (TA_CENTER, TA_JUSTIFY, TA_LEFT,
                                  ParagraphStyle, getSampleStyleSheet)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate
from sentence_transformers import SentenceTransformer
from sqlalchemy import and_

import src.dto as DTO
import src.models as Models
from utilities import build_filter

styles = getSampleStyleSheet()
styles['Normal'].fontName = 'TNR'
pdfmetrics.registerFont(TTFont('TNR', 'TNR.ttf', 'UTF-8'))

model_name = 'nanalysenko/DeepPavlov_for_Panacea'
model = SentenceTransformer(model_name)

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
            if tags_:
                tags_list = [i.strip().lower() for i in tags_.split(',')] 
                for tag in tags_list:
                    embedding = model.encode(tag.lower())
                    filtered_ids = list(set([row.id for row in db.query(Models.GQW_model.id).join(Models.GQW_model.tag_gqw).join(Models.GQW_tag.vector_id).filter(Models.GQW_vector.vector.cosine_distance(embedding) < 0.41).all()]))
                    filter_dict['id'].extend(filtered_ids)
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
    try:
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
            if db.query(Models.GQW_model).filter(Models.GQW_model.reference == data.reference).count():
                s1 = db.query(Models.GQW_model).filter(Models.GQW_model.reference == data.reference).update({'supervisor_id': n.id})
            else:
                s1 = Models.GQW_model(supervisor_id=n.id)
                db.add(s1)
            db.commit()
        return 'The data is downloaded'
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
            if not db.query(Models.GQW_model).filter(Models.GQW_model.theme== file.filename).count():
                filepath_full = r'/Backend/app/full_pdf'
                filepath_compressed = r'/Backend/app/compressed'

                contents = file.file
                inputpdf = PdfReader(contents)
                output = PdfWriter()

                len_pdf = len(inputpdf.pages)
                if len_pdf > 92:
                    len_pdf = 92
                
                for i in range(1, len_pdf):
                    if i in range(1, 5):
                        if not re.search(r'ЗАДАНИЕ\s+НА\s+', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                            if re.search(r'аннотация', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                                output.add_page(inputpdf.pages[i])
                    if i in range(5, len_pdf-30):
                        output.add_page(inputpdf.pages[i])
                    if i in range(len_pdf-30, len_pdf):
                        if re.search(r'Приложени', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                            break
                        else:
                            output.add_page(inputpdf.pages[i])

                with open(os.path.join(filepath_full, file.filename), 'wb') as f:
                    output.write(f)
                list_word = ['аннотация',
                            'annotation', 'abstract']
                
                title = extract_text(contents, page_numbers=[0])
                text_ex = re.split(r'\n\n', title, 4)
                text_ex[4] = text_ex[4].replace('\n', '')
                theme=''
                if re.search(r'(.*?)Выпускная', text_ex[4]):
                    theme = re.search(
                        r'(.*?)Выпускная', text_ex[4]).group(1).strip().upper()
                    if re.search(r'<|>|^«|»$', theme):
                        theme = re.sub(r'<|>|^«|»$', '', theme)
                    if 'НАЗВАНИЕ ТЕМЫ РАБОТЫ:' in theme:
                        theme = theme.replace(
                            'НАЗВАНИЕ ТЕМЫ РАБОТЫ:', '').replace('<', '').replace('>', '').strip().upper()
                    if 'НАПРИМЕРЕ' in theme:
                        theme = theme.replace('НАПРИМЕРЕ', 'НА ПРИМЕРЕ').strip().upper()
                    if re.search(r'УДК(.*?)\)', theme):
                        res = str(re.search(r'УДК(.*?)\)', theme).group(0))
                        theme = theme.split(res)[-1]
                    if file.filename == 'Kokov.pdf':
                        theme = theme.replace('КОКОВ АЛЕКСАНДР АНДРЕЕВИЧ', '')

                qualification = ''
                if re.search(r'подготовки\s+(.*?)\s+Международные', title):
                    if re.search(r'подготовки\s+(.*?)\s+Международные', title).group(1) == '41.03.05':
                        qualification = 'Бакалавриат'
                    elif re.search(r'подготовки\s+(.*?)\s+Международные', title).group(1) == '41.04.05':
                        qualification = 'Магистратура'
                text_merge = list(set([extract_text(contents, page_numbers=[i]) for i in range(1, 8) for w in list_word if not 'оглавление' in extract_text(contents, page_numbers=[i]).lower() if not 'содержание' in extract_text(contents, page_numbers=[i]).lower() if
                                        w in extract_text(contents, page_numbers=[i]).lower()]))

                text = (' '.join(text_merge)).replace(
                    '\n', ' ').replace('_', '').replace('\x0c', '')
                text = [re.sub(r'\d+$|(- )', '', i).strip() for i in re.split(
                    r'(Аннотация{1}|Abstract{1}|abstarct|Annotation|Оглавление|Содержание)', text, flags=re.IGNORECASE) if i]

                text = [i for i in text if i]

                text_rus = ['No data', 'No data']
                text_en = ['No data', 'No data']
                for j in range(len(text)):
                    if not re.search(r'.{1,}\s+\d+', text[j]):
                        if text[j].lower() in ['abstract', 'annotation', 'abstarct']:         
                            text_en[0] = text[j]
                            text_en[1] = text[j+1]
                        if text[j].lower() in ['аннотация']:
                            text_rus[0] = text[j]
                            text_rus[1] = text[j+1]
                            
                
                if text_rus:
                    if re.search(r'\d+$', text_rus[1]):
                        text_rus[1] = (re.sub(r'\d+$', '', text_rus[1])).strip()
                if text_en:
                    if re.search(r'\d+$', text_en[1]):
                        text_en[1] = (re.sub(r'\d+$', '', text_en[1])).strip()
                if not db.query(Models.GQW_qualification).filter(Models.GQW_qualification.qualification == qualification).count():
                    s7 = Models.GQW_qualification(qualification=qualification)
                    db.add(s7)
                    db.commit()
                
                tags_req = ''
                responce = ''
                if text_rus[1] != 'No data':
                    tags_req = requests.get('http://url/keyword_ext', params={'text':text_rus[1]})
                    if tags_req.status_code == 200:
                        responce = (tags_req.text).replace("\"", '').split(',')
                elif text_rus[1] == 'No data' and text_en[1] != 'No data':
                    text_rus[1] = text_en[1]
                    tags_req = requests.get('http://url/keyword_ext', params={'text':text_en[1]})
                    if tags_req.status_code == 200:
                        responce = (tags_req.text).replace("\"", '').split(',')
                qualification_request = db.query(Models.GQW_qualification).filter(Models.GQW_qualification.qualification == qualification).one()
                if db.query(Models.GQW_model).filter(Models.GQW_model.reference== file.filename).count(): 
                    if not db.query(Models.GQW_model).filter(Models.GQW_model.theme== theme).count():
                        s1 = db.query(Models.GQW_model).filter(Models.GQW_model.reference== str(file.filename)).update({'qualification_id': qualification_request.id, 'theme': theme, 'abstract': f'{text[1]}'})
                        db.commit()               
                    else:
                        return theme
                else:
                    if not db.query(Models.GQW_model).filter(Models.GQW_model.theme== theme).count():
                        s1 = Models.GQW_model(qualification_id=qualification_request.id, theme=theme, reference=file.filename, abstract=f'{text_rus[1]}')
                        db.add(s1)
                        db.commit()
                    else:
                        return theme
                updated_gqw_id= db.query(Models.GQW_model.id).filter(Models.GQW_model.reference == file.filename).one()

                if not responce == 'There is no text':
                    for tag in responce:
                        tag = tag.strip()
                        tag_ = f'{tag[0].upper()}{tag[1:]}'.strip()
                        if not db.query(Models.GQW_tag).filter(Models.GQW_tag.tag_name == tag_).count():
                            s2 = Models.GQW_tag(tag_name=str(tag_).strip())
                            db.add(s2)
                            db.commit()
                            sm = Models.Middle(vkr_id=updated_gqw_id.id, tags_id=s2.id)
                            db.add(sm)
                            s3 = Models.GQW_vector(vector=
                                model.encode(tag_.lower()), tag_id=s2.id)
                            db.add(s3)
                            db.commit()
                        else:
                            tags = db.query(Models.GQW_tag).filter(Models.GQW_tag.tag_name == tag_).one()
                            sm = Models.Middle(vkr_id=updated_gqw_id.id, tags_id=tags.id)
                            db.add(sm)
                            db.commit()
                else:
                    s_no_tag = Models.GQW_tag(tag_name='Нет доступных тэгов')
                    db.add(s_no_tag)
                    sm_no_tag = Models.Middle(vkr_id=updated_gqw_id.id, tags_id=s_no_tag.id)
                    db.add(sm_no_tag)
                    db.commit()

                doc = SimpleDocTemplate(os.path.join(filepath_compressed, file.filename), pagesize=A4)
                p1 = Paragraph(str(text_rus[0]).replace(
                    "\n", "<br />"), center_style)

                p2 = Paragraph(str(text_rus[1]).replace(
                    "\n", "<br />"), justify_style)
                p3 = Paragraph(str(text_en[0]).replace(
                    "\n", "<br />"), center_style)
                p4 = Paragraph(str(text_en[1]).replace(
                    "\n", "<br />"), justify_style)
                doc.build([p1, p2, p3, p4],)
                return 'The file is uploaded'
            else:
                return theme
        else:
            return 'Please, attach .pdf file'
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Something went wrong: {e}')
    finally:
        file.file.close()
        db.close()


def post_passkey(passkey: DTO.PassKey, db):
    try:
        charset='abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ0123456789'
        password_new = ''

        for i in range(8):
            password_new += charset[random.randint(0, len(charset)-1)]
        gqw_id_converted = uuid.UUID(passkey.gqw_id)
        if not db.query(Models.Visitor).filter(Models.Visitor.visitor_id == passkey.visitor_id).count():
            s1 = Models.Visitor(visitor_id = passkey.visitor_id)
            db.add(s1)
            db.commit()
        if not db.query(Models.PassKeys).filter(and_(Models.PassKeys.token_encoded == password_new, Models.PassKeys.gqw_id == gqw_id_converted, Models.PassKeys.visitor_f == passkey.visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())).count():
            s2 = Models.PassKeys(token_encoded = password_new, date_of_get=datetime.datetime.now(), date_expired=(datetime.datetime.now() + timedelta(days=1)), visitor_f= passkey.visitor_id, gqw_id= gqw_id_converted)
            db.add(s2)
            db.commit()
            return password_new
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
            return [[{'value': item.theme, 'label': item.theme} for item in db.query(Models.GQW_model.theme).distinct() if item.theme], [item.reference for item in db.query(Models.GQW_model.reference).distinct() if item.reference], [{'value':item.department, 'label':item.department} for item in db.query(Models.Supervisor_department.department).distinct() if item.department], [{'value':item.name, 'label':item.name} for item in db.query(Models.GQW_supervisor.name).distinct() if item.name], [{'value':item.degree, 'label':item.degree} for item in db.query(Models.Supervisor_degree.degree).distinct() if item.degree], [{'value':item.tag_name, 'label':item.tag_name} for item in db.query(Models.GQW_tag.tag_name).distinct() if item.tag_name if not item.tag_name in ['Нет доступных тэгов', 'There is no text', 'null']]]
        else:
            return 'No data'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()


def update_gqw(data, db):
    try:
        d={}
        if db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).join(Models.GQW_model.type_of_qualification).filter(Models.GQW_model.reference == data.reference).count():
            if data.supervisor:
                if db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).count():
                    supervisor_new = db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).one()
                    d['supervisor_id'] = supervisor_new.id
                else:
                    return f'supervisor - {data.supervisor} - is not searched'
            if data.qualification:
                if db.query(Models.GQW_qualification).filter(Models.GQW_qualification.qualification == data.qualification).count():
                    qualification_request = db.query(Models.GQW_qualification).filter(Models.GQW_qualification.qualification == data.qualification).one()
                    d['qualification_id'] = qualification_request.id
                else:
                    return f'qualification - {data.qualification} -  is not searched'
            if data.theme:
                d['theme'] = data.theme
            if data.abstract:
                d['abstract'] = data.abstract
            if d:
                s1 = db.query(Models.GQW_model).filter(Models.GQW_model.reference== data.reference).update(d)
                db.commit()  
            updated_gqw= db.query(Models.GQW_model).filter(Models.GQW_model.reference == data.reference).one()
            if data.tags:
                s_tag_delete= db.query(Models.Middle).filter(Models.Middle.vkr_id == updated_gqw.id).all()
                if s_tag_delete:
                    for i in s_tag_delete:
                        db.delete(i)
                        db.commit()
                data_tags = str(data.tags)
                for tag in data_tags.split(','):
                    tag = tag.strip()
                    if not db.query(Models.GQW_tag).filter(Models.GQW_tag.tag_name == tag).count():
                        s2 = Models.GQW_tag(tag_name=str(tag).strip())
                        db.add(s2)
                        db.commit()
                        sm = Models.Middle(vkr_id=updated_gqw.id, tags_id=s2.id)
                        db.add(sm)
                        s3 = Models.GQW_vector(vector=
                            model.encode(tag.lower()), tag_id=s2.id)
                        db.add(s3)
                        db.commit()
                    else:
                        tags = db.query(Models.GQW_tag).filter(Models.GQW_tag.tag_name == tag).one()
                        sm = Models.Middle(vkr_id=updated_gqw.id, tags_id=tags.id)
                        db.add(sm)
                        db.commit()
            return f'{data.reference} is updated'
        else:
            return f'Empty fields'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()

def update_supervisor(data, db):
    try:
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
            return f'{data.supervisor} is updated'
        else:
            n = db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).one()
            if n.degree_gqw.degree != data.degree:
                degree_new = db.query(Models.Supervisor_degree).filter(Models.Supervisor_degree.degree == data.degree).one()
                s0 = db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).update({'degree_id': degree_new.id})
                db.commit()
            if n.department_gqw.department != data.department:
                department_new = db.query(Models.Supervisor_department).filter(Models.Supervisor_department.department == data.department).one()
                s8 = db.query(Models.Supervisor_department).filter(Models.Supervisor_department.department == data.department).update({'department_id': department_new.id})
                db.commit()
            return f'{n.name} is updated'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()


def delete_gqw(data, db):
    try:
        if f'{data.reference}' in os.listdir('./app/compressed'):
            os.remove(f'./app/compressed/{data.reference}')
        if f'{data.reference}'in os.listdir('./app/full_pdf'):
            os.remove(f'./app/full_pdf/{data.reference}')

        if db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).join(Models.GQW_model.type_of_qualification).filter(Models.GQW_model.reference == data.reference).count():
            record = db.query(Models.GQW_model).join(Models.GQW_model.supervisor_gqw).join(Models.GQW_model.tag_gqw).join(Models.GQW_model.type_of_qualification).filter(Models.GQW_model.reference == data.reference).one()
            db.delete(record)
            db.commit()
            return f'{data.reference} is deleted'
        else:
            return f'{data.reference} is not present'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()
    

def delete_tag(data, db):
    try:
        if db.query(Models.GQW_tag).join(Models.GQW_vector).filter(Models.GQW_tag.tag_name == data.tag).count():
            record = db.query(Models.GQW_tag).join(Models.GQW_vector).filter(Models.GQW_tag.tag_name == data.tag).one()
            db.delete(record)
            db.commit()
            return f'{data.tag} is deleted'
        else:
            return f'{data.tag} is not present'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()


def delete_department(data, db):
    try:
        if db.query(Models.Supervisor_department).filter(Models.Supervisor_department.department == data.department).count():
            record = db.query(Models.Supervisor_department).filter(Models.Supervisor_department.department == data.department).one()
            db.delete(record)
            db.commit()
            return f'{data.department} is deleted'
        else:
            return f'{data.department} is not present'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()


def delete_degree(data, db):
    try:
        if db.query(Models.Supervisor_degree).filter(Models.Supervisor_degree.degree == data.degree).count():
            record = db.query(Models.Supervisor_degree).filter(Models.Supervisor_degree.degree == data.degree).one()
            db.delete(record)
            db.commit()
            return f'{data.degree} is deleted'
        else:
            return f'{data.degree} is not present'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()


def change_compressed_file(file, db):
    try:
        if file.filename.endswith('.pdf'):
            filepath_compressed = r'/Backend/app/compressed'
            contents = file.file
            with open(os.path.join(filepath_compressed, file.filename), 'wb') as buffer:
                shutil.copyfileobj(contents, buffer)
            return 'file is changed'
        else:
            return 'it is not .pdf file'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()

def change_full_file(file, db):
    try:
        if file.filename.endswith('.pdf'):
            filepath_full = r'/Backend/app/full_pdf'
            contents = file.file
            with open(os.path.join(filepath_full, file.filename), 'wb') as buffer:
                shutil.copyfileobj(contents, buffer)
            return 'file is changed'
        else:
            return 'it is not .pdf file'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()

def delete_supervisor(data, db):
    try:
        if db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).count():
            record = db.query(Models.GQW_supervisor).filter(Models.GQW_supervisor.name == data.supervisor).one()
            db.delete(record)
            db.commit()
            return f'{data.supervisor} is deleted'
        else:
            return f'{data.supervisor} is not present'
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
    finally:
        db.close()


def change_full():
    filepath = r'/Backend/app/full_pdf'
    for file in os.listdir(filepath):
        inputpdf = PdfReader(open(os.path.join(filepath, file), 'rb'))
        output = PdfWriter()

        len_pdf = len(inputpdf.pages)
        if len_pdf > 92:
            len_pdf = 92
        for i in range(1, len_pdf):
            if i in range(1, 4):
                if not re.search(r'ЗАДАНИЕ\s+НА\s+', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                    if len(inputpdf.pages[i].images) == 0:
                        output.add_page(inputpdf.pages[i])
            if i in range(4, len_pdf-30):
                output.add_page(inputpdf.pages[i])
            if i in range(len_pdf-30, len_pdf):
                if re.search(r'Приложени', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                    break
                else:
                    output.add_page(inputpdf.pages[i])
        with open(os.path.join(filepath, file), 'wb') as pdf:
            output.write(pdf)
            pdf.close()