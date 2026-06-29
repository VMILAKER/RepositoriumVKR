
import requests
from fastapi import (APIRouter, Depends, File, Header, HTTPException,
                     UploadFile, status)
from pydantic import Json
from sqlalchemy.ext.asyncio import AsyncSession

import config
import src.dto as DTO
import src.services as Service
from src.database import get_db_sql
from utilities import generate_presigned_url


async def verify_internal_api_key(
    x_internal_api_key: str | None = Header(None, alias='API-Key'),
) -> bool:
    internal_api_key = config.get_backend_api_key()

    if not x_internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Internal backend API key is missing',
        )

    if not internal_api_key or x_internal_api_key != internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid internal backend API key',
        )
    return True


router = APIRouter(
    dependencies=[Depends(verify_internal_api_key)],
    responses={
        401: {'description': 'Invalid or missing internal API key'},
    },
)
compressed_pdf_folder_path, abstract_folder_path = config.get_pdf_folders()


@router.get('/get_vkr', tags=['vkr'])
async def get(theme_: str = None, supervisor_: str = None, qualification_: str = None, tags_: str = None, db: AsyncSession = Depends(get_db_sql)):
    return await Service.get_vkr(theme_, supervisor_, qualification_, tags_, db)

@router.post('/upload_vkr', tags=['vkr'])
async def post(data: Json[DTO.GraduateQuallificationWork]= Depends(), file: UploadFile= File(...), db: AsyncSession = Depends(get_db_sql)):
    return await Service.upload_vkr(data, file, db)

@router.put('/update_vkr', tags=['vkr'])
async def update_data(data: DTO.GraduateQuallificationWork_update, db: AsyncSession = Depends(get_db_sql)):
    return await Service.update_vkr(data, db)

@router.delete('/delete_vkr', tags=['vkr'])
async def delete_data(data: DTO.DeleteGQW, db: AsyncSession = Depends(get_db_sql)):
    return await Service.delete_vkr(data, db)

@router.get('/get_vkr_by_passkey', tags=['vkr', 'passkey'])
async def search_passkey(password: str=None, vkr_id: str=None, visitor_id: str=None, db: AsyncSession = Depends(get_db_sql)):
    return await Service.get_passkey(password, vkr_id, visitor_id, db)

@router.get('/get_preloaded_data', tags=['vkr'])
async def preloaded_data(db: AsyncSession = Depends(get_db_sql)):
    return await Service.get_preloaded_data(db)

@router.put('/change_full_file', tags=['file_manipulation'])
async def change_full_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db_sql)):
    return Service.replace_file(compressed_pdf_folder_path, file, db)

# @router.put('/delete_private_data_full_file', tags=['file_manipulation'])
# async def change_private_data_file():
#     return Service.recreate_full_pdf_version()

@router.put('/change_compressed_file', tags=['file_manipulation'])
async def change_abstract_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db_sql)):
    return Service.replace_file(abstract_folder_path, file, db)

@router.post('/add_passkey', tags=['passkey'])
async def create_passkey(passkey: DTO.PassKey=None, db: AsyncSession = Depends(get_db_sql)):
    return await Service.post_passkey(passkey, db)


@router.put('/update_supervisor', tags=['supervisor_manipulation'])
async def update_supervisor(data: DTO.SupervisorUpdate, db: AsyncSession = Depends(get_db_sql)):
    return await Service.update_supervisor(data, db)

@router.delete('/delete_supervisor', tags=['supervisor_manipulation'])
async def delete_supervisor(data: DTO.DeleteSupervisor, db: AsyncSession = Depends(get_db_sql)):
    return await Service.delete_supervisor(data, db)


@router.delete('/delete_tag')
async def delete_tag(data: DTO.DeleteTag, db: AsyncSession = Depends(get_db_sql)):
    return await Service.delete_tag(data, db)

@router.delete('/delete_department')
async def delete_department(data: DTO.DeleteDepartment, db: AsyncSession = Depends(get_db_sql)):
    return await Service.delete_department(data, db)

@router.delete('/delete_degree')
async def delete_degree(data: DTO.DeleteDegree, db: AsyncSession = Depends(get_db_sql)):
    return await Service.delete_degree(data, db)


@router.post('/test_ollama')
async def test_ollama(text: str=None):
    try:
        if text != 'No data':
            payload= config._create_payload(text)
            tags_req = requests.post(config.get_ollama_api_url(),json=payload)
            print(tags_req.status_code)
            if tags_req.status_code == 200:
                return tags_req.json()
                # print(tags_req.json()['response'])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'{e}')
    
@router.post('test_minio_url')
async def test_url(filename: str=None, bucket_type: str='compressed'):
    return generate_presigned_url(filename, bucket_type)