from pydantic import BaseModel
from typing import Optional


class GraduateQuallificationWork(BaseModel):
    theme: str
    supervisor: str
    department: Optional[str] = None
    degree: Optional[str] = None
    type_of_qualification: str
    abstract: str
    reference: str
    tags: str
