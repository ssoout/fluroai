from __future__ import annotations

from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Patient


class PatientBase(BaseModel):
    full_name: str
    email: str
    birth_date: Optional[date] = None
    medical_record_number: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(PatientBase):
    pass


class PatientRead(PatientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Study


class StudyBase(BaseModel):
    patient_id: int
    taken_at: datetime
    priority: str = "routine"
    notes: Optional[str] = None
    image_path: Optional[str] = None


class StudyCreate(StudyBase):
    pass


class StudyUpdate(BaseModel):
    patient_id: Optional[int] = None
    taken_at: Optional[datetime] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    image_path: Optional[str] = None


class StudyRead(StudyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Analysis


class AnalysisResultBase(BaseModel):
    study_id: int
    ai_status: str
    ai_findings: str
    ai_confidence: Optional[float] = None


class AnalysisResultCreate(AnalysisResultBase):
    pass


class AnalysisResultRead(AnalysisResultBase):
    id: int
    ai_diagnosis: Optional[str] = None
    confirmation_status: str
    confirmation_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnalysisConfirmRequest(BaseModel):
    action: Literal["approve", "reject"] = "approve"
    notes: Optional[str] = None


class AnalysisResultDetail(BaseModel):
    result: AnalysisResultRead
    study: StudyRead
    patient: PatientRead

    class Config:
        from_attributes = True


class PendingResultItem(BaseModel):
    result_id: int
    patient_name: str
    taken_at: datetime
    ai_status: str
    ai_findings: str
    ai_confidence: Optional[float] = None
    confirmation_status: str


class PendingResultsResponse(BaseModel):
    items: List[PendingResultItem]


# ---------------------------------------------------------------------------
# Dashboard


class RecentResult(BaseModel):
    result_id: int
    patient_name: str
    taken_at: datetime = Field(..., description="Дата и время съемки")
    status: str
    findings: str
    confidence: float | None = None
    confirmation_status: str
    needs_manual_review: bool = False


class DashboardStats(BaseModel):
    processed: int = 0
    pathology_count: int = 0
    manual_review: int = 0


class AlertItem(BaseModel):
    result_id: int
    patient_name: str
    taken_at: datetime
    reason: str
    resolved: bool = False


class DashboardRecentResponse(BaseModel):
    items: List[RecentResult]


class DashboardAlertsResponse(BaseModel):
    items: List[AlertItem]

