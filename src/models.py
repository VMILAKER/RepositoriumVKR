import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, types
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.database import Base, engine


class GQW_model(Base):
    __tablename__ = 'gqw_data'

    id = Column(UUID(as_uuid=True), index=True,
                primary_key=True, default=uuid.uuid4)
    theme = Column(String, index=True)
    type_of_qualification = Column(String(12), index=True)
    abstract = Column(String)
    reference = Column(String)
    supervisor_id = Column(UUID, ForeignKey(
        'gqw_supervisors.id'), nullable=False)

    tag_gqw = relationship('GQW_tag', lazy='joined')
    supervisor_gqw = relationship('GQW_supervisor', foreign_keys=[
                                  supervisor_id], lazy='joined')


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
    gqw_id = Column(UUID(as_uuid=True), ForeignKey('gqw_data.id'))


class GQW_supervisor(Base):
    __tablename__ = 'gqw_supervisors'

    id = Column(UUID(as_uuid=True), index=True,
                default=uuid.uuid4, primary_key=True)
    name = Column(String)
    department = Column(String)
    degree = Column(String)


Base.metadata.create_all(engine)
