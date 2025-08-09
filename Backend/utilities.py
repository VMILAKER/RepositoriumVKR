from typing import List
import psycopg2.extras

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import joinedload, sessionmaker

import src.models as Models

model_name = 'sentence-transformers/all-MiniLM-L6-v2'
model = SentenceTransformer(model_name)
psycopg2.extras.register_uuid()


def insert_data_db():
    data = [
        {
            "supervisor": "Улизко М.С.",
            "type_of_qualification": "Бакалавриат",
            "tags": "Cargo",
            "theme": "Адаптивная модель грузоперевозок",
            "abstract": "Эта работа посвящена исследованию мирового грузового транспортного флота и разработке базы данных, содержащей актуальную информацию о его состоянии и характеристиках. В рамках работы будут выявлены и  проанализированы различные источники, предоставляющие данные о грузоперевозках, включая открытые интернет–ресурсы и реферативные базы данных. Собранные данные будут структурированы и использованы для проектирования схемы базы данных, которая позволит эффективно хранить и обрабатывать информацию. Также будет проведена аналитика международной системы грузоперевозок, что позволит глубже понять динамику и особенности функционирования грузового транспорта на уровне. Результаты работы могут быть полезны для специалистов в области логистики, транспортного менеджмента и исследований в сфере международной торговли.",
            "reference": 'Adaptive_Model.pdf'
        },
        {
            "supervisor": "Артамонов А.А.",
            "type_of_qualification": "Магистратура",
            "tags": "Science Landscape,Data Analysis",
            "theme": "Научно-технологический ландшафт",
            "abstract": "В работе представлена модель научно-технологического ландшафта как метод анализа научных публикаций. Рассматриваются существующие инструменты анализа, включая методологии оценки научно-технологического ландшафта, методологии формирования научного и патентного ландшафтов, а также математические методы классификации данных при анализе данных о научном прогрессе в рамках страны или отрасли. Рассматривается сбор, обработка и визуализация научных публикаций с помощью программных инструментов. В ходе работы составлено хранилище данных научных публикаций выбранных стран для апробации инструмента. Представлена методика разработки инструмента анализа научно-технологического ландшафта.",
            "reference": "Scientific_Technological_Landscape.pdf"
        },
        {
            "supervisor": "Улизко М.С.",
            "type_of_qualification": "Бакалавриат",
            "tags": "Affilation Unification,Data Processing",
            "theme": "Программное средство унификации аффилиаций",
            "abstract": "В научно-исследовательской работе рассматривается создание и возможность применения программного инструмента для определения и унификации названий научных организаций из научных публикаций. В работе проведен обзор существующих алгоритмов и технологий обработки аффилиаций, определены целевые составляющие аффилиаций, составлена схема базы данных определения и унификации наименований научных организаций, разработан и протестирован на точность алгоритм. На основе тестирования установлено, что с использованием программного инструмента возможно программное определение и унификация наименований научных организаций.",
            "reference": "Programme_Gear_Unification_Afillation.pdf"
        },
        {
            "supervisor": "Морозов Е.М.",
            "type_of_qualification": "Магистратура",
            "tags": "Nuclear sector,India,Government Policy",
            "theme": "Анализ ядерного энергетического сектора Индии",
            "abstract": "Работа направлена на ...",
            "reference": "Analysis_Nuclear_Sector_India.pdf"
        },
        {
            "supervisor": "Проничева Л.В.",
            "type_of_qualification": "Магистратура",
            "tags": "Risk analysis,Bank sector,Software",
            "theme": "Анализ рисков при импортозамещении программного обеспечения банковского сектора",
            "abstract": "Работа направлена на ...",
            "reference": "Analysis_Risk_bank_sector.pdf"
        },
        {
            "supervisor": "Кучинов В.П.",
            "type_of_qualification": "Бакалавриат",
            "tags": "Biogas,Environment",
            "theme": "Анализ биогаза и рынка биогазовых установок",
            "abstract": "Работа направлена на ...",
            "reference": "Analysis_Biogas.pdf"
        },
        {
            "supervisor": "Артамонов А.А.",
            "type_of_qualification": "Магистратура",
            "tags": "Graphs",
            "theme": "Метод выявления неявных связей на графах",
            "abstract": "Инструменты по визуализации позволяют преобразовать большие массивы данных в понятные графики для пользователя. В данной работе рассматривается разработка инструмента визуализации графов для выявления неявных связей между информационными объектами. В работе представлена реализация метода для выявления неявных связей между объектами и разработка инструмента для построения графовой визуализации, позволяющая пользователю взаимодействовать с графом посредством фильтрации. Реализованы функциональные возможности и предложен специализированный язык запросов для изменения вида узлов и ребер графа. Разработанный инструмент и предложенный метод апробированы на двух реальных наборах данных: обнаружение потенциальных нарушений обязательств по ядерному нераспространению, выявление перспективных направлений научного сотрудничества организаций, подтвердив практическую значимость данного исследования.",
            "reference": "Method_Implicit_Relations_Graphs.pdf"
        }
    ]
    supervisors = [
        {
            'name': "Артамонов А.А.",
            'department': "Кафедра 65 'Анализ конкурентных систем'",
            'degree': 'Кандидат технических наук'
        },
        {
            'name': "Улизко М.С.",
            'department': "Кафедра 65 'Анализ конкурентных систем'",
            'degree': 'Б/C'
        },
        {
            'name': "Морозов Е.М.",
            'department': "Кафедра 55 'Международные отношения'",
            'degree': 'Кандидат исторических наук'
        }
    ]
    POSTGRESQL_URL = "postgresql://postgres:kds041@localhost/postgres"
    engine = create_engine(POSTGRESQL_URL)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    try:
        l = []
        superv_dict_list = []
        superv_name_list = []
        for j in supervisors:
            if not j['name'] in superv_name_list:
                s4 = Models.GQW_supervisor(
                    name=j['name'], department=j['department'], degree=j['degree'])
                session.add(s4)
                session.commit()
                superv_name_list.append(j['name'])
        for i in data:
            req_super = session.query(
                Models.GQW_supervisor.id, Models.GQW_supervisor.name).all()
            for n in req_super:
                if i['supervisor'] == n[1]:
                    s1 = Models.GQW_model(theme=i['theme'], type_of_qualification=i
                                          ['type_of_qualification'], abstract=i['abstract'], reference=i['reference'], supervisor_id=n[0])
                    session.add(s1)
                    session.commit()
                    for tag in i['tags'].split(','):
                        if not tag in l:
                            s2 = Models.GQW_tag(tag_name=tag, gqw_id=s1.id)
                            session.add(s2)
                            session.commit()
                            s3 = Models.GQW_vector(vector=str(np.array(
                                model.encode(tag)).reshape(1, -1)), tag_id=s2.id)
                            session.add(s3)
                            session.commit()
                            l.append(tag)
        print('The data is downloaded')
        result = session.query(Models.GQW_model).options(
            joinedload(Models.GQW_model.tag_gqw), joinedload(Models.GQW_model.supervisor_gqw)).all()
        return result
    except Exception as e:
        print(f'Something wrong: {e}')

    finally:
        # cur.close()
        session.close()


def build_filter(session, filter_dict: dict) -> List:
    """The filter for dynamic search throughout database

    Args:
        session (_type_): Database session (ex. POSTGRESql)
        filter_dict (dict): The dictationary of dynamic filters

    Returns:
        List: List of filters for the request
    """
    filters = []
    for key, value in filter_dict.items():
        if value:
            print(f'{key}: {value}')
            if isinstance(filter_dict[key], list):
                if key in ['theme', 'supervisor']:
                    filter_theme = []
                    filter_superv = []
                    for item in filter_dict[key]:
                        if key == 'theme':
                            filter_theme.append(
                                (Models.GQW_model.theme.icontains(item)))
                        else:
                            filter_superv.append(
                                getattr(Models.GQW_supervisor, 'name') == item)
                    filters.append(or_(*filter_theme))
                    filters.append(or_(*filter_superv))
                else:
                    filters.append(
                        getattr(Models.GQW_model, key).in_(filter_dict[key]))
            else:
                filters.append(getattr(Models.GQW_model, key) == value)
        else:
            pass
    return filters


if __name__ == '__main__':
    insert_data_db()
