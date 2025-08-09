from typing import Annotated
from reportlab.lib.styles import getSampleStyleSheet

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

import src.services as Service
from src.database import get_db_sql
from src.dto import GraduateQuallificationWork

router = APIRouter()

db_dependency = Annotated[Session, Depends(get_db_sql)]

styles = getSampleStyleSheet()
# styles['Normal'].fontName = 'Gol'
# pdfmetrics.registerFont(TTFont('Gol', 'Gol.ttf', 'UTF-8'))


@router.get('/')
async def get(theme_: str = None, supervisor_: str = None, qualification_: str = Query(None, enum=['Бакалавриат', 'Магистратура']), tags_: str = None, db: Session = Depends(get_db_sql)):
    try:
        return Service.get_gqw_data_sql(theme_, supervisor_, qualification_, tags_, db)
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')


@router.post('/post')
async def post(data: GraduateQuallificationWork = None, db: Session = Depends(get_db_sql)):
    return Service.upload_gqw_data_sql(data, db)


@router.post('/create_file')
async def create_file(file: UploadFile = File(...)):
    return Service.upload_file(file)
