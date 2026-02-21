from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import src.dto as DTO
import src.services as Service
from src.database import get_db_sql

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db_sql)]

@router.get('/')
async def get(theme_: str = None, supervisor_: str = None, qualification_: str = None, tags_: str = None, db: Session = Depends(get_db_sql)):
    return Service.get_gqw_data_sql(theme_, supervisor_, qualification_, tags_, db)

@router.get('/get_gqw_by_passkey')
async def search_passkey(password: str=None, gqw_id: str=None, visitor_id: str=None, db: Session = Depends(get_db_sql)):
    return Service.get_passkey(password, gqw_id, visitor_id, db)

@router.get('/preloaded_data')
async def preloaded_data(db: Session = Depends(get_db_sql)):
    return Service.get_preloaded_data(db)

@router.post('/post')
async def post(data: DTO.GraduateQuallificationWork = None, db: Session = Depends(get_db_sql)):
    return Service.upload_gqw_data_sql(data, db)

@router.post('/create_file')
async def create_file(file: UploadFile = File(...), db: Session = Depends(get_db_sql)):
    return Service.upload_file(file, db)

@router.put('/change_full_file')
async def change_full_file(file: UploadFile = File(...), db: Session = Depends(get_db_sql)):
    return Service.change_full_file(file, db)

@router.put('/delete_private_data_full_file')
async def change_private_data_file():
    return Service.change_full()


@router.put('/change_compressed_file')
async def change_file(file: UploadFile = File(...), db: Session = Depends(get_db_sql)):
    return Service.change_compressed_file(file, db)

@router.post('/add_passkey')
async def create_passkey(passkey: DTO.PassKey=None, db: Session = Depends(get_db_sql)):
    return Service.post_passkey(passkey, db)

@router.put('/update_data')
async def update_data(data: DTO.GraduateQuallificationWork_update, db: Session = Depends(get_db_sql)):
    return Service.update_gqw(data, db)

@router.put('/update_supervisor')
async def update_supervisor(data: DTO.SupervisorUpdate, db: Session = Depends(get_db_sql)):
    return Service.update_supervisor(data, db)

@router.delete('/delete_gqw')
async def delete_data(data: DTO.DeleteGQW, db: Session = Depends(get_db_sql)):
    return Service.delete_gqw(data, db)

@router.delete('/delete_tag')
async def delete_tag(data: DTO.DeleteTag, db: Session = Depends(get_db_sql)):
    return Service.delete_tag(data, db)

@router.delete('/delete_supervisor')
async def delete_supervisor(data: DTO.DeleteSupervisor, db: Session = Depends(get_db_sql)):
    return Service.delete_supervisor(data, db)

@router.delete('/delete_department')
async def delete_department(data: DTO.DeleteDepartment, db: Session = Depends(get_db_sql)):
    return Service.delete_department(data, db)

@router.delete('/delete_degree')
async def delete_degree(data: DTO.DeleteDegree, db: Session = Depends(get_db_sql)):
    return Service.delete_degree(data, db)

