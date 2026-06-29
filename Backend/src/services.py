import datetime
import logging
import os
import re
import shutil
import tracemalloc
import uuid
from datetime import timedelta

import requests
from fastapi import HTTPException, status
from PyPDF2 import PdfReader, PdfWriter
from sentence_transformers import SentenceTransformer
from sqlalchemy import and_, func, select, update
from sqlalchemy.orm import joinedload

import config
import src.dto as DTO
import src.models as Models
import utilities as util

model_name = config.get_sentence_transformer_model_name()
model = SentenceTransformer(model_name)
tracemalloc.start()

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

compressed_pdf_folder_path, abstract_folder_path = config.get_pdf_folders()

async def get_preloaded_data(db):
    try:
        vkr_request = (await db.execute(select(Models.GQW_model)))
        if vkr_request.scalars().unique().all():
            return [[{'value': item, 'label': item} for item in (await db.execute(select(Models.GQW_model.theme))).scalars().unique().all() if item], [item for item in (await db.execute(select(Models.GQW_model.reference))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.Supervisor_department.department))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.GQW_supervisor.name))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.Supervisor_degree.degree))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.GQW_tag.tag_name))).scalars().unique().all() if item if item not in ['Нет доступных тэгов', 'There is no text', 'null']]]
        else:
            return 'No data'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')
    

async def get_vkr(theme_: str, supervisor_: str, qualification_: str, tags_: str, db):
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
        filter_dict = {}
        logger.info(filter_dict)
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
                filtered_ids = set()
                for tag in tags_list:
                    embedding = model.encode(tag.lower())
                    vkr_by_tag_request= await db.execute(select(Models.Middle.vkr_id).join(Models.GQW_tag, Models.GQW_tag.id == Models.Middle.tags_id).join(Models.GQW_vector, Models.GQW_tag.id == Models.GQW_vector.tag_id).where(Models.GQW_vector.vector.cosine_distance(embedding) < 0.41))
                    filtered_ids.update(vkr_by_tag_request.scalars().all())
                filter_dict['id'] = list(filtered_ids)
                if not filter_dict['id']:
                    return "No findings by tag's query"
        req = (await db.execute(select(Models.GQW_model).join(Models.GQW_supervisor, Models.GQW_model.supervisor_id == Models.GQW_supervisor.id).join(Models.Supervisor_department, Models.GQW_supervisor.department_id == Models.Supervisor_department.id).options(joinedload(Models.GQW_model.type_of_qualification), joinedload(Models.GQW_model.supervisor_gqw), joinedload(Models.GQW_model.supervisor_gqw).joinedload(Models.GQW_supervisor.department_gqw), joinedload(Models.GQW_model.supervisor_gqw).joinedload(Models.GQW_supervisor.degree_gqw),joinedload(Models.GQW_model.tag_gqw)).where(and_(*util.build_filter(filter_dict))))).scalars().unique().all()
        if len(list(req))>0:
            return [{
                'id':i.id,
                'theme': i.theme,
                'abstract': i.abstract,
                'qualification': i.type_of_qualification.qualification,
                'reference': i.reference,
                'supervisor': i.supervisor_gqw.name,
                'supervisor_department': i.supervisor_gqw.department_gqw.department,
                'supervisor_degree': i.supervisor_gqw.degree_gqw.degree,
                'tags': [tag.tag_name for tag in i.tag_gqw]
            } for i in req]
        else:
            return 'No data'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')

async def upload_vkr(data, file, db):
    try:
        filename= f'{util.generate_key()}.pdf'
        if (file.filename).endswith('.pdf'):
            filepath_abstract = abstract_folder_path
            filepath_compressed = compressed_pdf_folder_path
            contents = file.file

            async with db.begin():
                vkr_by_filename = (await db.execute(select(Models.GQW_model.id).where(Models.GQW_model.reference== filename))).scalars().unique().one_or_none()
                if not vkr_by_filename:
                    if data.department and data.degree:
                        department_request = await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))
                        degree_request = await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))
                        if not department_request.scalars().one_or_none():
                            add_department = Models.Supervisor_department(department=data.department)
                            db.add(add_department)
                            await db.flush()
                        if not degree_request.scalars().one_or_none():
                            add_degree = Models.Supervisor_degree(degree=data.degree)
                            db.add(add_degree)
                            await db.flush()
                    
                    supervisor_request = await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))
                    if not supervisor_request.scalars().one_or_none():
                        department = (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().one_or_none()
                        degree = (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().one_or_none()
                        if department and degree:
                            add_supervisor = Models.GQW_supervisor(
                                name=data.supervisor, department_id=department.id, degree_id=degree.id)
                            db.add(add_supervisor)
                            await db.flush()
                        else:
                            return 'Input department and degree of supervisor'


                    theme, text_rus, text_en, qualification = util.generate_vkr_card(contents)
                    
                    qualification_request= (await db.execute(select(Models.GQW_qualification).where(Models.GQW_qualification.qualification == qualification))).scalars().unique().one_or_none()
                    if not qualification_request:
                        add_qualification = Models.GQW_qualification(qualification=qualification)
                        db.add(add_qualification)
                        await db.flush()
                    
                    llm_response = 'No data'
                    if text_rus[1] != 'No data':
                        messages = config._create_payload(text_rus[1])
                        tags_extraction_request = requests.post(config.get_ollama_api_url(),json=messages)
                        if tags_extraction_request.status_code == 200:
                            responce_tags = tags_extraction_request.json()
                            llm_response = [f'{i[0].upper()}{i[1:]}'.strip() for i in responce_tags['message']['content'].split(',') if i]
                    qualification_request = (await db.execute(select(Models.GQW_qualification).where(Models.GQW_qualification.qualification == qualification))).scalars().unique().one_or_none()
                    supervisor_request = (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().unique().one_or_none()
                   
                    vkr_by_theme = (await db.execute(select(Models.GQW_model).where(Models.GQW_model.theme== theme))).scalars().unique().one_or_none()

                    if not vkr_by_theme:
                        add_vkr = Models.GQW_model(qualification_id=qualification_request.id, theme=theme, reference=filename, abstract=f'{text_rus[1]}', supervisor_id=supervisor_request.id)
                        db.add(add_vkr)
                        await db.flush()
                    else:
                        return 'GQW already exists'
                    updated_vkr_id= (await db.execute(select(Models.GQW_model.id).where(Models.GQW_model.reference == filename))).scalars().one_or_none()

                    if not llm_response == 'No data':
                        for tag in llm_response:
                            tag = f'{tag[0].upper()}{tag[1:]}'
                            tag_request = (await db.execute(select(Models.GQW_tag).where(Models.GQW_tag.tag_name == tag))).scalars().one_or_none()
                            if not tag_request:
                                add_tag = Models.GQW_tag(tag_name=str(tag).strip())
                                db.add(add_tag)
                                await db.flush()
                                
                                add_vkr_and_tag_relation = Models.Middle(vkr_id=updated_vkr_id, tags_id=add_tag.id)
                                db.add(add_vkr_and_tag_relation)
                                
                                add_vector = Models.GQW_vector(vector=
                                    model.encode(tag.lower()), tag_id=add_tag.id)
                                db.add(add_vector)
                                await db.flush()
                            else:
                                tags = (await db.execute(select(Models.GQW_tag).where(Models.GQW_tag.tag_name == tag))).scalars().one_or_none()
                                add_vkr_and_tag_relation = Models.Middle(vkr_id=updated_vkr_id, tags_id=tags.id)
                                db.add(add_vkr_and_tag_relation)
                                await db.flush()
                    else:
                        no_tag_for_vkr_request = (await db.execute(select(Models.GQW_tag.id).where(Models.GQW_tag.tag_name == 'Нет доступных тэгов'))).scalars().one_or_none()
                        if not no_tag_for_vkr_request:
                            add_no_tag_label = Models.GQW_tag(tag_name='Нет доступных тэгов')
                            db.add(add_no_tag_label)
                            await db.flush()
                            add_vkr_and_tag_relation = Models.Middle(vkr_id=updated_vkr_id, tags_id=add_no_tag_label.id)
                            await db.flush()
                        else:
                            add_vkr_and_tag_relation = Models.Middle(vkr_id=updated_vkr_id, tags_id=no_tag_for_vkr_request)
                            db.add(add_vkr_and_tag_relation)
                            await db.flush()
                    
                    util.create_compressed_vkr(contents, filename)
                    util.create_abstract_file(text_rus, text_en, filename)
                    return 'The file is uploaded'
                else:
                    return 'Filename already exists'
        else:
            return 'Please, attach .pdf file'
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Something went wrong: {e}')
    finally:
        file.file.close()



async def update_vkr(data, db):
    try:
        update_vkr_values_dict={}
        if (await db.execute(select(Models.GQW_model).options(joinedload(Models.GQW_model.type_of_qualification), joinedload(Models.GQW_model.supervisor_gqw), joinedload(Models.GQW_model.supervisor_gqw).joinedload(Models.GQW_supervisor.department_gqw), joinedload(Models.GQW_model.supervisor_gqw).joinedload(Models.GQW_supervisor.degree_gqw),joinedload(Models.GQW_model.tag_gqw)).where(Models.GQW_model.reference == data.reference))).scalars().unique().one_or_none():
            if data.supervisor:
                if (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().one_or_none():
                    supervisor = (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().one_or_none()
                    update_vkr_values_dict['supervisor_id'] = supervisor.id
                else:
                    return f'supervisor - {data.supervisor} - is not searched'
            if data.qualification:
                if (await db.execute(select(Models.GQW_qualification).where(Models.GQW_qualification.qualification == data.qualification))).scalars().one_or_none():
                    qualification = (await db.execute(select(Models.GQW_qualification).where(Models.GQW_qualification.qualification == data.qualification))).scalars().one_or_none()
                    update_vkr_values_dict['qualification_id'] = qualification.id
                else:
                    return f'qualification - {data.qualification} -  is not found'
            if data.theme:
                update_vkr_values_dict['theme'] = data.theme
            if data.abstract:
                update_vkr_values_dict['abstract'] = data.abstract
            if update_vkr_values_dict:
                await db.execute(update(Models.GQW_model).where(Models.GQW_model.reference== data.reference).values(update_vkr_values_dict))
                await db.commit()  
            
            vkr= (await db.execute(select(Models.GQW_model).where(Models.GQW_model.reference == data.reference))).scalars().one_or_none()
            if data.tags:
                vkr_unmatched_tags= (await db.execute(select(Models.Middle).where(Models.Middle.vkr_id == vkr.id))).scalars().all()
                if vkr_unmatched_tags:
                    for i in vkr_unmatched_tags:
                        await db.delete(i)
                        await db.commit()
                tags = str(data.tags)
                for tag in tags.split(','):
                    tag = tag.strip()
                    if not (await db.execute(select(Models.GQW_tag).where(Models.GQW_tag.tag_name == tag))).scalars().one_or_none():
                        add_tag = Models.GQW_tag(tag_name=str(tag).strip())
                        db.add(add_tag)
                        await db.flush()
                        add_vkr_and_tag_relation = Models.Middle(vkr_id=vkr.id, tags_id=add_tag.id)
                        db.add(add_vkr_and_tag_relation)
                        add_vector = Models.GQW_vector(vector=
                            model.encode(tag.lower()), tag_id=add_tag.id)
                        db.add(add_vector)
                        await db.flush()
                    else:
                        tags = (await db.execute(select(Models.GQW_tag).where(Models.GQW_tag.tag_name == tag))).scalars().one_or_none()
                        add_vkr_and_tag_relation = Models.Middle(vkr_id=vkr.id, tags_id=tags.id)
                        db.add(add_vkr_and_tag_relation)
                        await db.flush()
            return f'{data.reference} is updated'
        else:
            return 'Empty fields'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')



async def update_supervisor(data, db):
    try:
        async with db.begin():
            if not (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().one_or_none():
                add_department = Models.Supervisor_department(department=data.department)
                db.add(add_department)
                await db.flush()
            if not (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().one_or_none():
                add_degree = Models.Supervisor_degree(degree=data.degree)
                db.add(add_degree)
                await db.flush()
            if not (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().one_or_none():
                departemnt = (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().one_or_none()
                degree = (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().one_or_none()

                add_supervisor = Models.GQW_supervisor(
                    name=data.supervisor, department_id=departemnt.id, degree_id=degree.id)
                db.add(add_supervisor)
                await db.flush()
                return f'{data.supervisor} is uploaded'
            else:
                supervisor = (await db.execute(select(Models.GQW_supervisor).options(joinedload(Models.GQW_supervisor.degree_gqw), joinedload(Models.GQW_supervisor.department_gqw)).where(Models.GQW_supervisor.name == data.supervisor))).scalars().one_or_none()
                if supervisor.degree_gqw.degree != data.degree:
                    degree_new = (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().one_or_none()
                    if supervisor:
                        supervisor.degree_id = degree_new.id
                        await db.flush()
                if supervisor.department_gqw.department != data.department:
                    department_new = (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().one_or_none()
                    if supervisor:
                        supervisor.department_id = department_new.id
                        await db.flush()
                return f'{supervisor.name} is updated'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')


async def post_passkey(passkey: DTO.PassKey, db):
    try:
        password = util.generate_key()

        vkr_id_converted = uuid.UUID(passkey.vkr_id)
        async with db.begin():
            visitor_request = await db.execute(select(Models.Visitor).where(Models.Visitor.visitor_id == passkey.visitor_id))
            if not visitor_request.scalars().one_or_none():
                s1 = Models.Visitor(visitor_id = passkey.visitor_id)
                db.add(s1)
                await db.flush()

            passkey_request = await db.execute(select(Models.PassKeys).where(and_(Models.PassKeys.token_encoded == password, Models.PassKeys.gqw_id == vkr_id_converted, Models.PassKeys.visitor_f == passkey.visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())))
            if not passkey_request.scalars().one_or_none():
                s2 = Models.PassKeys(token_encoded = password, date_of_get=datetime.datetime.now(), date_expired=(datetime.datetime.now() + timedelta(days=1)), visitor_f= passkey.visitor_id, vkr_id= vkr_id_converted)
                db.add(s2)
                await db.flush()
                return password
            else:
                return 'Password is already created and valid'
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Something went wrong: {e}')


async def get_passkey(password: str, vkr_id: str, visitor_id, db):
    try:
        passkey_request = await db.execute(select(Models.PassKeys).join(Models.Visitor).where(and_(Models.PassKeys.visitor_f == visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())))
        if visitor_id and passkey_request.scalars().unique().all():
            return [{'id': f'{item}'} for item in (await db.execute(select(Models.PassKeys.gqw_id).join(Models.Visitor).where(and_(Models.PassKeys.visitor_f == visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())))).scalars().unique().all()]
        if vkr_id:
            vkr_id_converted = uuid.UUID(vkr_id)
            passkey_request_with_vkr_id = await db.execute(select(Models.PassKeys).join(Models.Visitor).where(and_(Models.PassKeys.gqw_id == vkr_id_converted,  Models.PassKeys.token_encoded == password, Models.PassKeys.date_expired >= datetime.datetime.now())))
            if passkey_request_with_vkr_id.scalars().one_or_none():  
                return [{'id': f'{item}'} for item in (await db.execute(select(Models.PassKeys.gqw_id).join(Models.Visitor).where(and_(Models.PassKeys.gqw_id == vkr_id_converted,  Models.PassKeys.token_encoded == password, Models.PassKeys.date_expired >= datetime.datetime.now())))).scalars().unique().all()]
            else:
                return 'Unvalid key'
        else:
            return 'No data'
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Something went wrong: {e}')


async def delete_vkr(data, db):
    try:
        if f'{data.reference}' in os.listdir(compressed_pdf_folder_path):
            os.remove(f'{compressed_pdf_folder_path}/{data.reference}')
        if f'{data.reference}'in os.listdir(abstract_folder_path):
            os.remove(f'{abstract_folder_path}/{data.reference}')

        if (await db.execute(select(Models.GQW_model).where(Models.GQW_model.reference == data.reference))).scalars().first():
            vkr = (await db.execute(select(Models.GQW_model).where(Models.GQW_model.reference == data.reference))).scalars().first()
            await db.delete(vkr)
            await db.commit()
            return f'{data.reference} is deleted'
        else:
            return f'{data.reference} is not present'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')

    

async def delete_tag(data, db):
    try:
        if (await db.scalar(select(func.count(Models.GQW_tag.id)))) > 2:
            if (await db.execute(select(Models.GQW_tag).join(Models.GQW_vector).where(Models.GQW_tag.tag_name == data.tag))).scalars().one_or_none():
                tag = (await db.execute(select(Models.GQW_tag).join(Models.GQW_vector).where(Models.GQW_tag.tag_name == data.tag))).scalars().one()
                await db.delete(tag)
                await db.commit()
                return f'{data.tag} is deleted'
            else:
                return f'{data.tag} is not present'
        else:
            return 'Cannot delete because only 1 tag remains'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')



async def delete_department(data, db):
    try:
        if (await db.scalar(select(func.count(Models.Supervisor_department.id)))) > 2:
            if (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().one_or_none():
                department = (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().one()
                await db.delete(department)
                await db.commit()
                return f'{data.department} is deleted'
            else:
                return f'{data.department} is not present'
        else:
            return 'Cannot delete because only 1 department remains'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')



async def delete_degree(data, db):
    try:
        if (await db.scalar(select(func.count(Models.Supervisor_degree.id)))) > 2:
            if (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().one_or_none():
                degree = (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().one()
                await db.delete(degree)
                await db.commit()
                return f'{data.degree} is deleted'
            else:
                return f'{data.degree} is not present'
        else:
            return 'Cannot delete because only 1 degree remains'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')


async def delete_supervisor(data, db):
    try:
        if (await db.scalar(select(func.count(Models.GQW_supervisor.id)))) > 2:
            if (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().one_or_none():
                supervisor = (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().one()
                await db.delete(supervisor)
                await db.commit()
                return f'{data.supervisor} is deleted'
            else:
                return f'{data.supervisor} is not present'
        else:
            return 'Cannot delete because only 1 supervisor remains'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')


async def replace_file(folder_name, file, db):
    try:
        if file.filename.endswith('.pdf'):
            filename_from_db = (await db.execute(select(Models.GQW_model.reference).where(Models.GQW_model.reference == file.filename))).scalars().one_or_none()
            if filename_from_db:
                contents = file.file
                with open(os.path.join(folder_name, file.filename), 'wb') as buffer:
                    shutil.copyfileobj(contents, buffer)
                return 'file is changed'
            else:
                return 'No such file in database'
        else:
            return 'it is not .pdf file'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')




def recreate_full_pdf_version():
    for file in os.listdir(compressed_pdf_folder_path):
        input_pdf = PdfReader(open(os.path.join(compressed_pdf_folder_path, file), 'rb'))
        output = PdfWriter()

        len_pdf = len(input_pdf.pages)
        if len_pdf > 92:
            len_pdf = 92
        for i in range(1, len_pdf):
            if i in range(1, 4):
                if not re.search(r'ЗАДАНИЕ\s+НА\s+', input_pdf.pages[i].extract_text(), flags=re.IGNORECASE):
                    if len(input_pdf.pages[i].images) == 0:
                        output.add_page(input_pdf.pages[i])
            if i in range(4, len_pdf-30):
                output.add_page(input_pdf.pages[i])
            if i in range(len_pdf-30, len_pdf):
                if re.search(r'Приложени', input_pdf.pages[i].extract_text(), flags=re.IGNORECASE):
                    break
                else:
                    output.add_page(input_pdf.pages[i])
        with open(os.path.join(compressed_pdf_folder_path, file), 'wb') as pdf:
            output.write(pdf)
            pdf.close()