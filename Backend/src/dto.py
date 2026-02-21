from typing import Optional

from pydantic import BaseModel


class GraduateQuallificationWork(BaseModel):
    supervisor: str
    department: Optional[str] = None
    degree: Optional[str] = None
    reference: str

class PassKey(BaseModel):
    visitor_id: str
    gqw_id: str

class CheckPassword(BaseModel):
    password: str
    gqw_id: str

class GraduateQuallificationWork_update(BaseModel):
    theme: Optional[str] = None
    supervisor: Optional[str] = None
    reference: str
    abstract: Optional[str] = None
    qualification: Optional[str] = None
    tags: Optional[str] = None

class SupervisorUpdate(BaseModel):
    supervisor: str
    department: str
    degree: str

class DeleteGQW(BaseModel):
    reference: str

class DeleteTag(BaseModel):
    tag:str

class DeleteSupervisor(BaseModel):
    supervisor:str

class DeleteDepartment(BaseModel):
    department:str

class DeleteDegree(BaseModel):
    degree:str