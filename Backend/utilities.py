import json
import random
import re
from datetime import timedelta
from io import BytesIO
from typing import List

import psycopg2.extras
from pdfminer.high_level import extract_text
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate
from sqlalchemy import or_

import config
import src.models as Models

psycopg2.extras.register_uuid()




def build_filter(filter_dict: dict) -> List:
    """The filter for dynamic search throughout database

    Args:
        filter_dict (dict): The dictationary of dynamic filters

    Returns:
        List: List of filters for the request
    """
    filters = []
    for key, value in filter_dict.items():
        if value:
            if isinstance(filter_dict[key], list):
                if key in ['theme', 'supervisor']:
                    filter_theme = []
                    filter_superv = []
                    for item in filter_dict[key]:
                        if key == 'theme':
                            filter_theme.append(
                                (Models.GQW_model.theme.icontains(item)))
                        if key == 'supervisor':
                            filter_superv.append(
                                getattr(Models.GQW_supervisor, 'name') == item)
                    filters.append(or_(*filter_theme))
                    filters.append(or_(*filter_superv))
                else:
                    filters.append(
                        getattr(Models.GQW_model, key).in_(filter_dict[key]))
            else:
                if key =='type_of_qualification':
                    filters.append(getattr(Models.GQW_qualification, 'qualification') == value)
                else:
                    filters.append(getattr(Models.GQW_model, key) == value)
    return filters


def generate_vkr_card(contents):
    list_word = ['аннотация',
                'annotation', 'abstract']
    
    title = extract_text(contents, page_numbers=[0])
    title_cleaned = re.split(r'\n\n', title, 4)
    title_cleaned[4] = title_cleaned[4].replace('\n', '')
    
    theme=''
    if re.search(r'(.*?)Выпускная', title_cleaned[4]):
        theme = re.search(
            r'(.*?)Выпускная', title_cleaned[4]).group(1).strip().upper()
        if re.search(r'<|>|^«|»$', theme):
            theme = re.sub(r'<|>|^«|»$', '', theme)
        if 'НАЗВАНИЕ ТЕМЫ РАБОТЫ:' in theme:
            theme = theme.replace(
                'НАЗВАНИЕ ТЕМЫ РАБОТЫ:', '').replace('<', '').replace('>', '').strip().upper()
        if 'НАПРИМЕРЕ' in theme:
            theme = theme.replace('НАПРИМЕРЕ', 'НА ПРИМЕРЕ').strip().upper()
        if re.search(r'УДК(.*?)\)', theme):
            res = str(re.search(r'УДК(.*?)\)', theme).group(0))
            theme = theme.split(res)[-1]

    qualification = ''
    if re.search(r'подготовки\s+(.*?)\s+Международные', title):
        if re.search(r'подготовки\s+(.*?)\s+Международные', title).group(1) == '41.03.05':
            qualification = 'Бакалавриат'
        elif re.search(r'подготовки\s+(.*?)\s+Международные', title).group(1) == '41.04.05':
            qualification = 'Магистратура'
    
    text_merge = list(set([extract_text(contents, page_numbers=[i]) for i in range(1, 8) for w in list_word if 'оглавление' not in extract_text(contents, page_numbers=[i]).lower() if 'содержание' not in extract_text(contents, page_numbers=[i]).lower() if
                            w in extract_text(contents, page_numbers=[i]).lower()]))
    text = (' '.join(text_merge)).replace(
        '\n', ' ').replace('_', '').replace('\x0c', '')
    text = [re.sub(r'\d+$|(- )', '', i).strip() for i in re.split(
        r'(Аннотация{1}|Abstract{1}|abstarct|Annotation|Оглавление|Содержание)', text, flags=re.IGNORECASE) if i]

    text = [i for i in text if i]

    text_rus = ['No data', 'No data']
    text_en = ['No data', 'No data']
    for j in range(len(text)):
        if not re.search(r'.{1,}\s+\d+', text[j]):
            if text[j].lower() in ['abstract', 'annotation', 'abstarct']:         
                text_en[0] = text[j]
                text_en[1] = text[j+1]
            if text[j].lower() in ['аннотация']:
                text_rus[0] = text[j]
                text_rus[1] = text[j+1]
                
    if text_rus:
        if re.search(r'\d+$', text_rus[1]):
            text_rus[1] = (re.sub(r'\d+$', '', text_rus[1])).strip()
    if text_en:
        if re.search(r'\d+$', text_en[1]):
            text_en[1] = (re.sub(r'\d+$', '', text_en[1])).strip()

    return theme, text_rus, text_en, qualification


def create_abstract_file(rus_text:list, en_text:list, filename:str):
    buffer = BytesIO()

    styles = config.TextStyles()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    p1 = Paragraph(str(rus_text[0]).replace(
        "\n", "<br />"), styles.get_center_style())

    p2 = Paragraph(str(rus_text[1]).replace(
        "\n", "<br />"), styles.get_justify_style())
    p3 = Paragraph(str(en_text[0]).replace(
        "\n", "<br />"), styles.get_center_style())
    p4 = Paragraph(str(en_text[1]).replace(
        "\n", "<br />"), styles.get_justify_style())
    doc.build([p1, p2, p3, p4],)
    upload_file_minio(filename, buffer.getvalue(), config.get_bucket_name('abstract'))
    buffer.close()


def create_compressed_vkr(contents, filename):
    buffer = BytesIO()

    inputpdf = PdfReader(contents)
    output = PdfWriter()

    len_pdf = len(inputpdf.pages)
    if len_pdf > 92:
        len_pdf = 92
    
    for i in range(1, len_pdf):
        if i in range(1, 5):
            if not re.search(r'ЗАДАНИЕ\s+НА\s+', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                if re.search(r'аннотация', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                    output.add_page(inputpdf.pages[i])
        if i in range(5, len_pdf-30):
            output.add_page(inputpdf.pages[i])
        if i in range(len_pdf-30, len_pdf):
            if re.search(r'Приложени', inputpdf.pages[i].extract_text(), flags=re.IGNORECASE):
                break
            else:
                output.add_page(inputpdf.pages[i])
    output.write(buffer)
    upload_file_minio(filename, buffer.getvalue(), config.get_bucket_name('compressed'))
    buffer.close()


def generate_key():
    charset='abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNOPQRSTUVWXYZ0123456789'
    password_new = ''

    for i in range(8):
        password_new += charset[random.randint(0, len(charset)-1)]
    
    return password_new


def upload_file_minio(filename:str, file_data, bucket_name_env:str):
        client = config.minio_client()

        bucket_name = config.get_bucket_name(bucket_name_env)

        found = client.bucket_exists(bucket_name)
        if not found:
            client.make_bucket(bucket_name)
            print("Created bucket", bucket_name)
        else:
            print("Bucket", bucket_name, "already exists")
        public_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }

        # 3. Apply the policy to the bucket
        client.set_bucket_policy(bucket_name, json.dumps(public_policy))
        if hasattr(file_data, 'seek'):
            file_data.seek(0)
        if isinstance(file_data, bytes):
            data_to_upload = file_data
            file_length = len(file_data)
        # else:
        #     if hasattr(file_data, 'seek'):
        #         file_data.seek(0)
        #     data_to_upload = file_data
        #     file_length = len(data_to_upload)
    
        client.put_object(
            bucket_name=bucket_name, object_name=filename, data=BytesIO(data_to_upload), length=file_length, content_type='application/pdf', metadata={"Content-Disposition": "inline"} 
        )
        return 'Success'


def generate_presigned_url(filename:str, bucket_type:str):
    client = config.minio_client()
    
    return client.presigned_get_object(
        bucket_name=config.get_bucket_name(bucket_type),
        object_name=filename,
        expires=timedelta(minutes=120)
    )