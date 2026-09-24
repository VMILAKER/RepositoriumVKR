from fastapi import (APIRouter, Depends, File, Header, HTTPException,
                     UploadFile, status)
from sqlalchemy.ext.asyncio import AsyncSession

import config
import src.dto as DTO
import src.services as Service
from src.database import get_db_sql


async def verify_internal_api_key(
    x_internal_api_key: str | None = Header(None, alias='API_Key'),
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


@router.get('/get_vkr', tags=['vkr'])
async def get(theme: str=None, supervisor: str=None, qualification: str=None, tags: str=None, db: AsyncSession = Depends(get_db_sql)):
    return await Service.get_vkr(theme, supervisor, qualification, tags, db)

@router.post('/upload_vkr', tags=['vkr'])
async def post(data: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db_sql)):
    model = DTO.GraduateQuallificationWork.model_validate_json(data)
    return await Service.upload_vkr(model, file, db)

@router.put('/update_vkr', tags=['vkr'])
async def update_data(data: DTO.GraduateQuallificationWork_update, db: AsyncSession = Depends(get_db_sql)):
    return await Service.update_vkr(data, db)

@router.delete('/delete_vkr', tags=['vkr'])
async def delete_data(data: DTO.DeleteGQW, db: AsyncSession = Depends(get_db_sql)):
    return await Service.delete_vkr(data, db)

@router.get('/get_initial_passkeys', tags=['passkey'])
async def search_all_passkeys(visitor_id: str, db: AsyncSession = Depends(get_db_sql)):
    return await Service.get_initial_passkeys(visitor_id, db)

@router.get('/get_vkr_by_passkey', tags=['passkey'])
async def search_passkey(password: str=None, vkr_id: str=None, db: AsyncSession = Depends(get_db_sql)):
    return await Service.get_vkr_by_password(password, vkr_id, db)

@router.get('/get_preloaded_data', tags=['vkr'])
async def preloaded_data(db: AsyncSession = Depends(get_db_sql)):
    return await Service.get_preloaded_data(db)

@router.put('/change_compressed_file', tags=['file_manipulation'])
async def change_full_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db_sql)):
    return Service.replace_file(config.get_bucket_name(config.BucketNameTemplates.COMPRESSED), file, db)


@router.put('/change_abstract_file', tags=['file_manipulation'])
async def change_abstract_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db_sql)):
    return Service.replace_file(config.get_bucket_name(config.BucketNameTemplates.ABSTRACT), file, db)

@router.post('/add_passkey', tags=['passkey'])
async def create_passkey(passkey: DTO.PassKey, db: AsyncSession = Depends(get_db_sql)):
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


@router.get('/get_file/{filename}', tags=['file_manipulation'])
async def get_file_from_minio(filename: str=None, bucket_type: str=None):
    return await Service.get_file_minio(filename, bucket_type)