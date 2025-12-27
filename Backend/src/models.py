import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column
# from pgvector.sqlalchemy import Vector

from src.database import Base

class Middle(Base):
    __tablename__ = 'model_tag'

    id= Column(Integer, index=True, primary_key=True)
    vkr_id = Column(UUID(as_uuid=True), ForeignKey('gqw_data.id'))
    tags_id = Column(Integer, ForeignKey('gqw_tags.id'))


class GQW_model(Base):
    __tablename__ = 'gqw_data'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    theme = Column(String, index=True)
    qualification_id  = Column(Integer, ForeignKey('gqw_qualifications.id'), nullable=False)
    type_of_qualification = relationship('GQW_qualification', lazy='joined') 
    abstract = Column(String)
    reference = Column(String)
    supervisor_id = Column(UUID, ForeignKey(
        'gqw_supervisors.id'), nullable=False)

    tag_gqw = relationship('GQW_tag', secondary='model_tag', back_populates='gqw_id', lazy='joined')
    supervisor_gqw = relationship('GQW_supervisor', lazy='joined')

class GQW_qualification(Base):
    __tablename__ = 'gqw_qualifications'

    id = Column(Integer, index=True, primary_key=True)
    qualification = Column(String(12))


class GQW_vector(Base):
    __tablename__ = 'gqw_vectors'

    id = Column(Integer, index=True, primary_key=True)
    vector = Column(String)

    tag_id = Column(Integer, ForeignKey('gqw_tags.id'))


class GQW_tag(Base):
    __tablename__ = 'gqw_tags'

    id = Column(Integer, index=True, primary_key=True)
    tag_name = Column(String)

    vector_id = relationship("GQW_vector", lazy='joined')
    gqw_id = relationship('GQW_model', secondary='model_tag', back_populates='tag_gqw')


class GQW_supervisor(Base):
    __tablename__ = 'gqw_supervisors'

    id = Column(UUID(as_uuid=True), index=True,
                default=uuid.uuid4, primary_key=True)
    name = Column(String)

    department_id = Column(Integer, ForeignKey('supervisor_department.id'))
    department_gqw = relationship('Supervisor_department', lazy='joined')

    degree_id = Column(Integer, ForeignKey('supervisor_degree.id'))
    degree_gqw = relationship('Supervisor_degree', lazy='joined')

class Supervisor_department(Base):
    __tablename__ = 'supervisor_department'

    id = Column(Integer, index=True, primary_key=True)
    department = Column(String)


class Supervisor_degree(Base):
    __tablename__ = 'supervisor_degree'

    id = Column(Integer, index=True, primary_key=True)
    degree = Column(String)


class PassKeys(Base):
    __tablename__ = 'pass_key'

    id = Column(UUID(as_uuid=True), index=True,
                default=uuid.uuid4, primary_key=True)
    token_encoded = Column(String)
    date_of_get = Column(DateTime)
    date_expired = Column(DateTime)
    gqw_id = Column(UUID(as_uuid=True), index=True)
 
    visitor_f= Column(String, ForeignKey('visitor_data.visitor_id'))
    visitor_gqw = relationship('Visitor', lazy='joined')
    
class Visitor(Base):
    __tablename__ = 'visitor_data'

    id = Column(UUID(as_uuid=True), index=True,
                default=uuid.uuid4)
    visitor_id = Column(String, index=True, primary_key=True)