import uuid

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base


class Middle(Base):
    __tablename__ = 'model_tag'

    id= Column(Integer, index=True, primary_key=True)
    vkr_id = Column(UUID(as_uuid=True), ForeignKey('gqw_data.id'))
    tags_id = Column(UUID(as_uuid=True), ForeignKey('gqw_tags.id'))


class GQW_model(Base):
    __tablename__ = 'gqw_data'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    theme = Column(String, index=True)
    
    qualification_id  = Column(UUID(as_uuid=True), ForeignKey('gqw_qualifications.id'))
    type_of_qualification = relationship('GQW_qualification', lazy='raise_on_sql') 
    
    abstract = Column(String)
    reference = Column(String)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey(
        'gqw_supervisors.id'))
    supervisor_gqw = relationship('GQW_supervisor', lazy='raise_on_sql')

    tag_gqw = relationship('GQW_tag', secondary='model_tag', back_populates='gqw_id', lazy='raise_on_sql')
    

    # cascade="all, delete-orphan"

class GQW_qualification(Base):
    __tablename__ = 'gqw_qualifications'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    qualification = Column(String)


class GQW_vector(Base):
    __tablename__ = 'gqw_vectors'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    vector = Column(VECTOR(768))

    tag_id = Column(UUID(as_uuid=True), ForeignKey('gqw_tags.id'))
    tag = relationship("GQW_tag", back_populates='vector_id')

class GQW_tag(Base):
    __tablename__ = 'gqw_tags'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    tag_name = Column(String)

    vector_id = relationship("GQW_vector", back_populates='tag', lazy='raise_on_sql')
    gqw_id = relationship('GQW_model', secondary='model_tag', back_populates='tag_gqw')


class GQW_supervisor(Base):
    __tablename__ = 'gqw_supervisors'

    id = Column(UUID(as_uuid=True), index=True,
                default=uuid.uuid4, primary_key=True)
    name = Column(String)

    department_id = Column(UUID(as_uuid=True), ForeignKey('supervisor_department.id'))
    department_gqw = relationship('Supervisor_department', lazy='raise_on_sql')

    degree_id = Column(UUID(as_uuid=True), ForeignKey('supervisor_degree.id'))
    degree_gqw = relationship('Supervisor_degree', lazy='raise_on_sql')

class Supervisor_department(Base):
    __tablename__ = 'supervisor_department'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    department = Column(String, nullable=False)


class Supervisor_degree(Base):
    __tablename__ = 'supervisor_degree'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    degree = Column(String, nullable=False)


class PassKeys(Base):
    __tablename__ = 'pass_key'

    id = Column(UUID(as_uuid=True), index=True,
                default=uuid.uuid4, primary_key=True)
    token_encoded = Column(String)
    date_of_get = Column(DateTime)
    date_expired = Column(DateTime)
    gqw_id = Column(UUID(as_uuid=True), index=True)
 
    visitor_f= Column(String, ForeignKey('visitor_data.visitor_id'))
    visitor_gqw = relationship('Visitor', lazy='raise_on_sql')
    
class Visitor(Base):
    __tablename__ = 'visitor_data'

    id = Column(UUID(as_uuid=True), index=True,
                default=uuid.uuid4)
    visitor_id = Column(String, index=True, primary_key=True)