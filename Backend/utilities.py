from typing import List

import numpy as np
import psycopg2.extras
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import joinedload, sessionmaker

import src.models as Models

psycopg2.extras.register_uuid()


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

