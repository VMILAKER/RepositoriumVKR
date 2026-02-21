import json
import os
import re

import fitz
from qwen_vl_utils import process_vision_info
from transformers import (AutoModelForCausalLM, AutoProcessor, AutoTokenizer,
                          Qwen2_5_VLForConditionalGeneration)

model = AutoModelForCausalLM.from_pretrained("google/gemma-3-1b-it").to('cuda')
tokenizer = AutoTokenizer.from_pretrained("google/gemma-3-1b-it")


model_name = 'Qwen/Qwen2.5-VL-3B-Instruct'
model_parsing = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_name, torch_dtype='auto', device_map='auto')

processor = AutoProcessor.from_pretrained(model_name)


def keyword_extraction(text: str):
    messages = [
        {"role": "user",
         "content": [
             {'type': 'text', 'text': text},
             {'type': 'text',
              'text': "Выдели от четырех до восьми ключевых слов в том числе именованные сущности из текста, которые отражают его тематику. Представь их в виде списка слов через запятую, все слова должны быть полными (то есть не допускается обрыв слова). Напиши только список и без нумерации, тэги должны быть в именительном падеже,исключи одиночные прилагательные (т.е. те которые не связаны в с существительным) из списка ключевых слов. Если тэг не является именем собственным или аббревиатурой, то он должен быть в нижнем регистре"}
         ]
         },
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to('cuda')

    outputs = model.generate(**inputs, max_new_tokens=40)
    responce = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])
    if not 'Пожалуйста, предоставьте текст' in responce:
        responce = re.sub(r"\n*<end_of_turn>", '', responce).replace('"', '').replace(
            ']', '').replace('[', '').replace('\n', '').replace('*', '').replace('.', '').replace("\"", '')
        return responce
    else:
        return 'There is no text'


def parsing_title(path):
    list_data = []
    for i in os.listdir(path):
        doc = fitz.open(os.path.join(path, i))
        page = doc.load_page(1)
        pix = page.get_pixmap()
        pix.save(f"page.png")

        path_im = r'page.png'
        messages = [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'image': path_im
                    },
                    {'type': 'text',
                        'text': 'Выдели из текста следующие данные: тема, студент, кафедра, место выполнения работы, ФИО руководителя. Представь их в виде списка в формате ["тема", "студент", "кафедра", "место выполнения работы", "ФИО руководителя"], все слова должны быть полными (то есть не допускается обрыв слова). Не добавляй специальных символов в ответ, порядок в списке изменять нельзя, выводи все найденные значения как они отображены в тексте. Если нет одного элемента из данных, то пиши для этого элемента "No data".'}
                ],
            }
        ]

        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(text=[text], images=image_inputs,
                           videos=video_inputs, padding=True, return_tensors='pt')
        inputs = inputs.to('cuda')
        generated_ids = model_parsing.generate(**inputs, max_new_tokens=128)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(
            inputs.input_ids, generated_ids)]

        output_text = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)
        output_text[0] = output_text[0].replace(
            ']', '').replace('[', '').replace('"', '')
        data = output_text[0].split(',')
        if len(data) == 5:
            data_gqw = {
                'theme': str(data[0]),
                'student': str(data[1]),
                'department': str(data[2]),
                'place_of_working': str(data[3]),
                'supervisor': str(data[4])
            }
            list_data.append(data_gqw)
        output_text = re.sub(r'\"', '"', output_text[0])
        os.remove('page.png')

        print(f'{i} is done', output_text)
    with open('gqw_data_for_directory.json', 'w', encoding='utf-8') as f:
        json.dump(list_data, f, indent=2, ensure_ascii=False)
