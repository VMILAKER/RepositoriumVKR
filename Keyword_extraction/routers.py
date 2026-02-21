import services as Service
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get('/generation')
async def generate_keywords(text: str = None):
    try:
        return Service.keyword_extraction(text)
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')


@router.get('/parsing')
async def parse_gqw_data(text: str = None):
    try:
        return Service.parsing_title(text)
    except Exception as e:
        HTTPException(
            status_code='502', detail=f'Sorry, the server is not available. The error is {e}')
