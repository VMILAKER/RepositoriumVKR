import os
from enum import Enum

from dotenv import load_dotenv
from miniopy_async import Minio
from reportlab.lib.styles import (TA_CENTER, TA_JUSTIFY, TA_LEFT,
                                  ParagraphStyle, getSampleStyleSheet)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv()

class BucketNameTemplates(str, Enum):
    COMPRESSED = 'true'
    ABSTRACT = 'false'


def get_frontend_url():
    frontend_url_internal = os.getenv('INTERNAL_FRONTEND_URL')
    frontend_url_external = os.getenv('EXTERNAL_FRONTEND_URL')
    frontend_port = os.getenv('FRONTEND_PORT')
    if frontend_url_internal and frontend_port and frontend_url_external:
        return [frontend_url_internal, frontend_url_external, f'172.7.0.1:{frontend_port}', f"http://0.0.0.0:{frontend_port}",f"http://localhost:{frontend_port}"]
    else:
        ValueError('frontend_urls or PORT are missing')


def get_database_url():
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    name = os.getenv('DB_NAME')

    for i in [user, password, name]:
        if not i:
            raise ValueError('DB_USER or DB_PASSWORD or DB_NAME missed')
    return f'postgresql+asyncpg://{user}:{password}@postgres-repositorium/{name}'


def get_tag_extraction_report():
    prompt = os.getenv('TAG_EXTRACTION_PROMPT')
    if prompt:
        return prompt
    else:
        raise ValueError('No prompt provided')


def create_payload(text:str):
    model_name = os.getenv('LLM_NAME')
    temperature = os.getenv('LLM_TEMPERATURE')
    if model_name and temperature:
        return {
                "model": model_name,
                "messages":[{
                    "role": "user",
                    "content":  f'{text}\n\n{get_tag_extraction_report()}'
                    },],
                "stream": False,
                "tempetature": float(temperature)
        }
    else:
        raise ValueError('No LLM_NAME or LLM_TEMPERATURE provided')


def get_ollama_api_url():
    ollama_port = os.getenv('OLLAMA_PORT')
    if ollama_port:
        return f"http://ollama:{ollama_port}/api/chat"
    else:
        raise ValueError('No mention about OLLAMA_PORT')


def get_sentence_transformer_model_name():
    model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL_NAME")
    if model_name:
        return model_name
    else:
        raise ValueError('No name for SENTENCE_TRANSFORMER_MODEL_NAME')


class TextStyles():
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles['Normal'].fontName = 'TNR'
        pdfmetrics.registerFont(TTFont('TNR', 'fonts/TNR.ttf', 'UTF-8'))

    def get_justify_style(self):
        return ParagraphStyle(
                name="JustifiedStyle", parent=self.styles["Normal"], alignment=TA_JUSTIFY, leading=24, spaceAfter=24, firstLineIndent=25, fontSize=14)
    def get_center_style(self):
        return ParagraphStyle(
                name="CenteredStyle", parent=self.styles["Normal"], alignment=TA_CENTER, spaceAfter=10, fontSize=16)
    def get_left_style(self):
        return ParagraphStyle(
                name="CenteredStyle", parent=self.styles["Normal"], alignment=TA_LEFT, fontSize=12)
    

def get_backend_api_key():
    if os.getenv('INTERNAL_BACKEND_API_KEY'):
        return os.getenv('INTERNAL_BACKEND_API_KEY')
    

def minio_client():
    access_key = os.getenv('MINIO_ROOT_USER')
    secret_key = os.getenv('MINIO_ROOT_PASSWORD')

    return Minio(endpoint="minio:9000",
        access_key=access_key,
        secret_key=secret_key,
        secure=False 
    )


def get_bucket_name(is_compressed_type):
    if is_compressed_type == BucketNameTemplates.COMPRESSED:
        return os.getenv('MINIO_BUCKET_NAME_COMPRESSED') 
    elif is_compressed_type == BucketNameTemplates.ABSTRACT:
        return os.getenv('MINIO_BUCKET_NAME_ABSTRACT')
    else:
        raise ValueError('Bucket name is not provided or False')
    

def get_max_num_pages_in_vkr():
    max_num_pages = os.getenv("MAX_PAGES_IN_GQW")
    if max_num_pages:
        return int(max_num_pages)
    else:
        raise ValueError('MAX_PAGES_IN_GQW is not provided')