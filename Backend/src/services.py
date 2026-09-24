import datetime
import logging
import os
import shutil
import tracemalloc
import uuid
from datetime import timedelta
from io import BytesIO

import requests
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
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

logging.getLogger().setLevel(logging.INFO)


async def get_preloaded_data(db):
    try:
        vkr_request = (await db.execute(select(Models.GQW_model)))
        if vkr_request.scalars().unique().all():
            return [[{'value': item, 'label': item} for item in (await db.execute(select(Models.GQW_model.theme))).scalars().unique().all() if item], 
                    [item for item in (await db.execute(select(Models.GQW_model.reference))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.Supervisor_department.department))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.GQW_supervisor.name))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.Supervisor_degree.degree))).scalars().unique().all() if item], 
                    [{'value':item, 'label':item} for item in (await db.execute(select(Models.GQW_tag.tag_name))).scalars().unique().all() if item if item not in ['Нет доступных тэгов', 'There is no text', 'null']]]
        else:
            return [[{'value': 'No data', 'label': 'No data'}],
                    ['No data',],
                    [{'value': 'No data', 'label': 'No data'}],
                    [{'value': 'No data', 'label': 'No data'}],
                    [{'value': 'No data', 'label': 'No data'}],
                    [{'value': 'No data', 'label': 'No data'}]]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')
    

async def get_vkr(theme: str, supervisor: str, qualification: str, tags: str, db):
    try:
        async with db.begin():
            filter_dict = {}
            if qualification:
                filter_dict['type_of_qualification'] = qualification
            if theme:
                filter_dict['theme'] = [str(i.strip())
                                        for i in theme.split(',') if i]
            if supervisor:
                filter_dict['supervisor'] = [str(i.strip())
                                            for i in supervisor.split(',') if i]
            if tags:
                    tags_list = [i.strip().lower() for i in tags.split(',')] 
                    filtered_ids = set()
                    for tag in tags_list:
                        embedding = model.encode(tag.lower())
                        vkr_by_tag_request= await db.execute(select(Models.Middle.vkr_id).join(Models.GQW_tag, Models.GQW_tag.id == Models.Middle.tags_id).join(Models.GQW_vector, Models.GQW_tag.id == Models.GQW_vector.tag_id).where(Models.GQW_vector.vector.cosine_distance(embedding) < 0.41))
                        filtered_ids.update(vkr_by_tag_request.scalars().all())
                    filter_dict['id'] = list(filtered_ids)
                    if not filter_dict['id']:
                        return "No findings by tag's query"
            req = (await db.execute(select(Models.GQW_model).join(Models.GQW_qualification, Models.GQW_model.qualification_id == Models.GQW_qualification.id).join(Models.GQW_supervisor, Models.GQW_model.supervisor_id == Models.GQW_supervisor.id).join(Models.Supervisor_department, Models.GQW_supervisor.department_id == Models.Supervisor_department.id).options(joinedload(Models.GQW_model.type_of_qualification), joinedload(Models.GQW_model.supervisor_vkr), joinedload(Models.GQW_model.supervisor_vkr).joinedload(Models.GQW_supervisor.department_vkr), joinedload(Models.GQW_model.supervisor_vkr).joinedload(Models.GQW_supervisor.degree_vkr),joinedload(Models.GQW_model.tag_vkr)).where(and_(*util.build_filter(filter_dict))))).scalars().unique().all()
            if len(list(req))>0:
                await util.create_logs(Models.ElementTemplates.VKR, ' '.join([f'{num}){str(i.id)}\n' for num, i in enumerate(req)]), Models.StatusTemplates.VIEW, db)
                return [{
                    'id':i.id,
                    'theme': i.theme,
                    'abstract': i.abstract,
                    'qualification': i.type_of_qualification.qualification,
                    'reference': i.reference,
                    'supervisor': i.supervisor_vkr.name,
                    'supervisor_department': i.supervisor_vkr.department_vkr.department,
                    'supervisor_degree': i.supervisor_vkr.degree_vkr.degree,
                    'tags': [tag.tag_name for tag in i.tag_vkr]
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
            contents = file.file

            async with db.begin():
                vkr_by_filename = (await db.execute(select(Models.GQW_model.id).where(Models.GQW_model.reference== filename))).scalars().unique().one_or_none()
                if not vkr_by_filename:
                    theme, text_rus, text_en, qualification = util.generate_vkr_card(contents)

                    vkr_by_theme = (await db.execute(select(Models.GQW_model).where(Models.GQW_model.theme== theme))).scalars().unique().one_or_none()  

                    if not vkr_by_theme:
                        supervisor_request = (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().unique().one_or_none()
                        qualification_request = (await db.execute(select(Models.GQW_qualification).where(Models.GQW_qualification.qualification == qualification))).scalars().unique().one_or_none()  

                        if data.department and data.degree:
                            department_request = (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department)))
                            degree_request = (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree)))
                            if not department_request.scalars().unique().one_or_none():
                                add_department = Models.Supervisor_department(department=data.department)
                                db.add(add_department)
                                await db.flush()
                            if not degree_request.scalars().unique().one_or_none():
                                add_degree = Models.Supervisor_degree(degree=data.degree)
                                db.add(add_degree)
                                await db.flush()
                        
                        
                        if not supervisor_request:
                            department = (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().unique().one_or_none()
                            degree = (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().unique().one_or_none()
                            if department and degree:
                                add_supervisor = Models.GQW_supervisor(
                                    name=data.supervisor, department_id=department.id, degree_id=degree.id)
                                db.add(add_supervisor)
                                await db.flush()
                            else:
                                return 'Input department and degree of supervisor'
                            
                        if not qualification_request:
                            add_qualification = Models.GQW_qualification(qualification=qualification)
                            db.add(add_qualification)
                            await db.flush()

                        qualification = (await db.execute(select(Models.GQW_qualification).where(Models.GQW_qualification.qualification == qualification))).scalars().unique().one_or_none()  
                        supervisor = (await db.execute(select(Models.GQW_supervisor).where(Models.GQW_supervisor.name == data.supervisor))).scalars().unique().one_or_none()

                        add_vkr = Models.GQW_model(qualification_id=qualification.id, theme=theme, reference=filename, abstract=f'{text_rus[1]}', supervisor_id=supervisor.id)
                        db.add(add_vkr)
                        await db.flush()
                        
                        llm_response = 'No data'
                        if text_rus[1] != 'No data':
                            messages = config.create_payload(text_rus[1])
                            tags_extraction_request = requests.post(config.get_ollama_api_url(),json=messages)
                            if tags_extraction_request.status_code == 200:
                                responce_tags = tags_extraction_request.json()
                                llm_response = [f'{i[0].upper()}{i[1:]}'.strip() for i in responce_tags['message']['content'].split(',') if i]

                        
                        if not llm_response == 'No data':
                            for tag in llm_response:
                                tag = f'{tag[0].upper()}{tag[1:]}'
                                tag_request = (await db.execute(select(Models.GQW_tag).where(Models.GQW_tag.tag_name == tag))).scalars().one_or_none()
                                if not tag_request:
                                    add_tag = Models.GQW_tag(tag_name=str(tag).strip())
                                    db.add(add_tag)
                                    await db.flush()
                                    
                                    add_vkr_and_tag_relation = Models.Middle(vkr_id=add_vkr.id, tags_id=add_tag.id)
                                    db.add(add_vkr_and_tag_relation)
                                    
                                    add_vector = Models.GQW_vector(vector=
                                        model.encode(tag.lower()), tag_id=add_tag.id)
                                    db.add(add_vector)
                                    await db.flush()
                                else:
                                    tags = (await db.execute(select(Models.GQW_tag).where(Models.GQW_tag.tag_name == tag))).scalars().one_or_none()
                                    add_vkr_and_tag_relation = Models.Middle(vkr_id=add_vkr.id, tags_id=tags.id)
                                    db.add(add_vkr_and_tag_relation)
                                    await db.flush()
                        else:
                            no_tag_for_vkr_request = (await db.execute(select(Models.GQW_tag.id).where(Models.GQW_tag.tag_name == 'Нет доступных тэгов'))).scalars().one_or_none()
                            if not no_tag_for_vkr_request:
                                add_no_tag_label = Models.GQW_tag(tag_name='Нет доступных тэгов')
                                db.add(add_no_tag_label)
                                await db.flush()
                                add_vkr_and_tag_relation = Models.Middle(vkr_id=add_vkr.id, tags_id=add_no_tag_label.id)
                                await db.flush()
                            else:
                                add_vkr_and_tag_relation = Models.Middle(vkr_id=add_vkr.id, tags_id=no_tag_for_vkr_request)
                                db.add(add_vkr_and_tag_relation)
                                await db.flush()
                        
                        await util.create_compressed_vkr(contents, filename)
                        await util.create_abstract_file(text_rus, text_en, filename)
                        await util.create_logs(Models.ElementTemplates.VKR, str(add_vkr.id), Models.StatusTemplates.UPLOADED, db)
                        return 'The file is uploaded'
                    else:
                        return theme
                else:
                    return 'Filename already exists'
        else:
            return 'Please, attach .pdf file'
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Something went wrong: {e}')
    finally:
        file.file.close()


async def update_vkr(data, db):
    try:
        update_vkr_values_dict={}
        if (await db.execute(select(Models.GQW_model).options(joinedload(Models.GQW_model.type_of_qualification), joinedload(Models.GQW_model.supervisor_vkr), joinedload(Models.GQW_model.supervisor_vkr).joinedload(Models.GQW_supervisor.department_vkr), joinedload(Models.GQW_model.supervisor_vkr).joinedload(Models.GQW_supervisor.degree_vkr),joinedload(Models.GQW_model.tag_vkr)).where(Models.GQW_model.reference == data.reference))).scalars().unique().one_or_none():
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
            await util.create_logs(Models.ElementTemplates.VKR, str(vkr.id), Models.StatusTemplates.UPDATED, db)
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
                supervisor = (await db.execute(select(Models.GQW_supervisor).options(joinedload(Models.GQW_supervisor.degree_vkr), joinedload(Models.GQW_supervisor.department_vkr)).where(Models.GQW_supervisor.name == data.supervisor))).scalars().one_or_none()
                if supervisor.degree_vkr.degree != data.degree:
                    degree_new = (await db.execute(select(Models.Supervisor_degree).where(Models.Supervisor_degree.degree == data.degree))).scalars().one_or_none()
                    if supervisor:
                        supervisor.degree_id = degree_new.id
                        await db.flush()
                if supervisor.department_vkr.department != data.department:
                    department_new = (await db.execute(select(Models.Supervisor_department).where(Models.Supervisor_department.department == data.department))).scalars().one_or_none()
                    if supervisor:
                        supervisor.department_id = department_new.id
                        await db.flush()
                await util.create_logs(Models.ElementTemplates.SUPERVISOR, str(supervisor.id), Models.StatusTemplates.UPDATED, db)
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
                add_visitor = Models.Visitor(visitor_id = passkey.visitor_id)
                db.add(add_visitor)
                await db.flush()

            passkey_request = await db.execute(select(Models.PassKeys).where(and_(Models.PassKeys.token_encoded == password, Models.PassKeys.vkr_id == vkr_id_converted, Models.PassKeys.visitor_fk == passkey.visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())))
            if not passkey_request.scalars().one_or_none():
                add_passkey = Models.PassKeys(token_encoded = password, date_of_get=datetime.datetime.now(), date_expired=(datetime.datetime.now() + timedelta(days=1)), visitor_fk= passkey.visitor_id, vkr_id= vkr_id_converted)
                db.add(add_passkey)
                await db.flush()
                await util.create_logs(Models.ElementTemplates.PASSKEY, str(add_passkey.id), Models.StatusTemplates.UPLOADED, db)
                return password
            else:
                return 'Password is already created and valid'
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Something went wrong: {e}')


async def get_initial_passkeys(visitor_id:str, db):
    try:
        passkey_request = await db.execute(select(Models.PassKeys).join(Models.Visitor).where(and_(Models.PassKeys.visitor_fk == visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())))
        if visitor_id and passkey_request.scalars().unique().all():
            return [{'id': f'{item}'} for item in (await db.execute(select(Models.PassKeys.vkr_id).join(Models.Visitor).where(and_(Models.PassKeys.visitor_fk == visitor_id, Models.PassKeys.date_expired >= datetime.datetime.now())))).scalars().unique().all()]
        else:
            return 'No data'
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Something went wrong: {e}')


async def get_vkr_by_password(password: str, vkr_id: str, db):
    try:
        if password:
            vkr_id_converted = uuid.UUID(vkr_id)
            passkey_request_with_vkr_id = await db.execute(select(Models.PassKeys).join(Models.Visitor).where(and_(Models.PassKeys.vkr_id == vkr_id_converted,  Models.PassKeys.token_encoded == password, Models.PassKeys.date_expired >= datetime.datetime.now())))
            if passkey_request_with_vkr_id.scalars().one_or_none():  
                await util.create_logs(Models.ElementTemplates.VKR, vkr_id, Models.StatusTemplates.VIEW, db)
                return [{'id': f'{item}'} for item in (await db.execute(select(Models.PassKeys.vkr_id).join(Models.Visitor).where(and_(Models.PassKeys.vkr_id == vkr_id_converted,  Models.PassKeys.token_encoded == password, Models.PassKeys.date_expired >= datetime.datetime.now())))).scalars().unique().all()]
            else:
                return 'Unvalid key'
        else:
            return 'No data'
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Something went wrong: {e}')


async def delete_vkr(data, db):
    try:
        bucket_name_compressed = config.get_bucket_name('true')
        bucket_name_abstract = config.get_bucket_name('false')

        async with config.minio_client() as session:
            await session.remove_object(bucket_name_compressed, data.vkr_filename)
            await session.remove_object(bucket_name_abstract, data.vkr_filename)
            logging.info(f'{data.vkr_filename} deleted')

        if (await db.execute(select(Models.GQW_model).where(Models.GQW_model.reference == data.vkr_filename))).scalars().first():
            vkr = (await db.execute(select(Models.GQW_model).where(Models.GQW_model.reference == data.vkr_filename))).scalars().first()
            await util.create_logs(Models.ElementTemplates.VKR, str(vkr.id), Models.StatusTemplates.DELETED, db)
            await db.delete(vkr)
            await db.commit()
            return f'{data.vkr_filename} is deleted'
        else:
            return f'{data.vkr_filename} is not present'
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Sorry, the server is not available. The error is {e}')

    
async def delete_tag(data, db):
    try:
        if (await db.scalar(select(func.count(Models.GQW_tag.id)))) > 2:
            if (await db.execute(select(Models.GQW_tag).join(Models.GQW_vector).where(Models.GQW_tag.tag_name == data.tag))).scalars().one_or_none():
                tag = (await db.execute(select(Models.GQW_tag).join(Models.GQW_vector).where(Models.GQW_tag.tag_name == data.tag))).scalars().one()
                await util.create_logs(Models.ElementTemplates.TAG, str(tag.id), Models.StatusTemplates.DELETED, db)
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
                await util.create_logs(Models.ElementTemplates.DEPARTMENT, str(department.id), Models.StatusTemplates.DELETED, db)
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
                await util.create_logs(Models.ElementTemplates.DEGREE, str(degree.id), Models.StatusTemplates.DELETED, db)
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
                await util.create_logs(Models.ElementTemplates.SUPERVISOR, str(supervisor.id), Models.StatusTemplates.DELETED, db)
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
                await util.create_logs(Models.ElementTemplates.FILE, file.filename, Models.StatusTemplates.UPDATED, db)
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


async def get_file_minio(filename: str, is_compressed):
    try:
        async with config.minio_client() as client:
            bucket_name  = config.get_bucket_name(is_compressed)
            obj = await client.get_object(bucket_name, filename)
            data = await obj.read()
            obj.release()
            return StreamingResponse(BytesIO(data), media_type="application/pdf", headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'The error is {e}')


async def generate_presigned_url(filename:str, bucket_type:str):
    async with config.minio_client() as client:
        return await client.presigned_get_object(
            bucket_name=config.get_bucket_name(bucket_type),
            object_name=filename,
            expires=timedelta(minutes=10)
        )