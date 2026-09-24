import uuid
from enum import Enum

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


@staticmethod
def get_id():
    return Column(UUID(as_uuid=True),default=uuid.uuid4, primary_key=True)


class StatusTemplates(str, Enum):
    UPLOADED = 'uploaded'
    VIEW = 'viewed'
    DELETED = 'deleted'
    UPDATED = 'updated'


class ElementTemplates(str, Enum):
    VKR = 'vkr'
    TAG = 'tag'
    SUPERVISOR = 'supervisor'
    DEPARTMENT = 'department'
    DEGREE = 'degree'
    USER = 'user'
    PASSKEY = 'passkey'
    FILE = 'file'


class Middle(Base):
    __tablename__ = 'tag_vkr_wire'

    id= Column(Integer, index=True, primary_key=True)
    vkr_id = Column(UUID(as_uuid=True), ForeignKey('vkr_data.id'))
    tags_id = Column(UUID(as_uuid=True), ForeignKey('vkr_tags.id'))


class GQW_model(Base):
    __tablename__ = 'vkr_data'

    id = get_id()
    theme = Column(String, index=True)
    
    qualification_id  = Column(UUID(as_uuid=True), ForeignKey('vkr_qualifications.id'))
    type_of_qualification = relationship('GQW_qualification', lazy='raise_on_sql') 
    
    abstract = Column(String)
    reference = Column(String)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey(
        'vkr_supervisors.id'))
    supervisor_vkr = relationship('GQW_supervisor', lazy='raise_on_sql')

    tag_vkr = relationship('GQW_tag', secondary='tag_vkr_wire', back_populates='vkr_id', lazy='raise_on_sql')


class GQW_qualification(Base):
    __tablename__ = 'vkr_qualifications'

    id = get_id()
    qualification = Column(String)


class GQW_vector(Base):
    __tablename__ = 'vkr_vectors'

    id = get_id()
    vector = Column(VECTOR(768))

    tag_id = Column(UUID(as_uuid=True), ForeignKey('vkr_tags.id'))
    tag = relationship('GQW_tag', back_populates='vector_id')

class GQW_tag(Base):
    __tablename__ = 'vkr_tags'

    id = get_id()
    tag_name = Column(String)

    vector_id = relationship('GQW_vector', back_populates='tag', lazy='raise_on_sql')
    vkr_id = relationship('GQW_model', secondary='tag_vkr_wire', back_populates='tag_vkr')


class GQW_supervisor(Base):
    __tablename__ = 'vkr_supervisors'

    id = get_id()
    name = Column(String)

    department_id = Column(UUID(as_uuid=True), ForeignKey('supervisor_departments.id'))
    department_vkr = relationship('Supervisor_department', lazy='raise_on_sql')

    degree_id = Column(UUID(as_uuid=True), ForeignKey('supervisor_degrees.id'))
    degree_vkr = relationship('Supervisor_degree', lazy='raise_on_sql')



class Supervisor_department(Base):
    __tablename__ = 'supervisor_departments'

    id = get_id()
    department = Column(String, nullable=False)


class Supervisor_degree(Base):
    __tablename__ = 'supervisor_degrees'

    id = get_id()
    degree = Column(String, nullable=False)


class PassKeys(Base):
    __tablename__ = 'passkeys'

    id = get_id()
    token_encoded = Column(String)
    date_of_get = Column(DateTime)
    date_expired = Column(DateTime)
    vkr_id = Column(UUID(as_uuid=True), index=True)
 
    visitor_fk= Column(String, ForeignKey('visitors.visitor_id'))
    visitor_vkr = relationship('Visitor', lazy='raise_on_sql')

    
class Visitor(Base):
    __tablename__ = 'visitors'

    id = Column(UUID(as_uuid=True), index=True,
                    default=uuid.uuid4) 
    visitor_id = Column(String, index=True, primary_key=True)


class Log(Base):
    __tablename__ = 'logs'

    id = get_id()
    element = Column(String, index=True)
    element_id = Column(String, index=True)
    status = Column(String, index=True)
    datetime = Column(DateTime)