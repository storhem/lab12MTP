from datetime import datetime

from pydantic import BaseModel


class CertificateResponse(BaseModel):
    id: int
    student_id: int
    course_id: int
    enrollment_id: int
    certificate_number: str
    issued_at: datetime

    model_config = {"from_attributes": True}


class CertificateVerifyResponse(BaseModel):
    valid: bool
    certificate_number: str
    student_full_name: str
    course_title: str
    issued_at: datetime

    model_config = {"from_attributes": True}
