from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

import src.services as Service
from src.database import get_db_sql
from src.dto import GraduateQuallificationWork, PassKey

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db_sql)]

@router.get('/')
async def get(theme_: str = None, supervisor_: str = None, qualification_: str = None, tags_: str = None, db: Session = Depends(get_db_sql)):
    return Service.get_gqw_data_sql(theme_, supervisor_, qualification_, tags_, db)


@router.post('/post')
async def post(data: GraduateQuallificationWork = None, db: Session = Depends(get_db_sql)):
    return Service.upload_gqw_data_sql(data, db)


@router.post('/create_file')
async def create_file(file: UploadFile = File(...), db: Session = Depends(get_db_sql)):
    return Service.upload_file(file, db)


@router.post('/add_passkey')
async def create_passkey(passkey: PassKey=None, db: Session = Depends(get_db_sql)):
    return Service.post_passkey(passkey, db)


@router.get('/get_gqw_by_passkey')
async def search_passkey(password: str=None, gqw_id: str=None, visitor_id: str=None, db: Session = Depends(get_db_sql)):
    return Service.get_passkey(password, gqw_id, visitor_id, db)


@router.get('/preloaded_data')
async def preloaded_data(db: Session = Depends(get_db_sql)):
    return Service.get_preloaded_data(db)