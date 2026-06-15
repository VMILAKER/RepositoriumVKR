import os

from dotenv import load_dotenv
from reportlab.lib.styles import (TA_CENTER, TA_JUSTIFY, TA_LEFT,
                                  ParagraphStyle, getSampleStyleSheet)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv()



def get_frontend_url():
    return os.getenv('FRONTEND_URL')


def get_pdf_folders():
    compressed_pdf_folder_path = os.getenv('COMPRESSED_PDF_FOLDER_PATH')
    abstract_folder_path = os.getenv('ABSTRACT_FOLDER_PATH')

    return compressed_pdf_folder_path, abstract_folder_path


def get_database_url():
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    name = os.getenv('DB_NAME')

    return f'postgresql+asyncpg://{user}:{password}@postgres-repositorium/{name}'


def get_tag_extraction_report():
    prompt = os.getenv('TAG_EXTRACTION_PROMPT')
    if prompt:
        return prompt
    else:
        return 'No prompt provided'


def _create_payload(text:str):
    model_name = os.getenv('LLM_NAME')
    if model_name:
        return {
                "model": model_name,
                "messages":[{
                    "role": "user",
                    "content": [
                        {'type': 'text', 'text': text},
                        {'type': 'text','text': get_tag_extraction_report()}
                        ]
                    },],
                "stream":False
                }
    else:
        return 'No LLM_NAME is provided'


def get_ollama_api_url():
    ollama_port = os.getenv('OLLAMA_PORT')
    if ollama_port:
        return f"http://ollama:{ollama_port}/api/generate"
    else:
        return 'No mention about OLLAMA_PORT'


def get_sentence_transformer_model_name():
    model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL_NAME")
    if model_name:
        return model_name
    else:
        return 'No name for SENTENCE_TRANSFORMER_MODEL_NAME'


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