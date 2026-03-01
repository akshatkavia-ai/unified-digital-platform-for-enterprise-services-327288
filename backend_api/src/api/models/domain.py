from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApplicationCreateRequest(BaseModel):
    applicant_name: str = Field(..., description="Applicant display name.")
    service_code: str = Field(..., description="Service/module identifier for the application.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary application form payload.")


class ApplicationResponse(BaseModel):
    id: UUID = Field(..., description="Application id.")
    status: str = Field(..., description="Application lifecycle status.")
    applicant_name: str = Field(..., description="Applicant display name.")
    service_code: str = Field(..., description="Service/module identifier.")
    created_at: datetime = Field(..., description="Creation timestamp.")


class TaskCreateRequest(BaseModel):
    title: str = Field(..., description="Task title.")
    description: Optional[str] = Field(default=None, description="Task description.")
    application_id: Optional[str] = Field(default=None, description="Optional related application id.")
    assignee_user_id: Optional[str] = Field(default=None, description="Optional assignee user id.")


class TaskResponse(BaseModel):
    id: str = Field(..., description="Task id.")
    title: str = Field(..., description="Task title.")
    status: str = Field(..., description="Task status.")
    created_at: datetime = Field(..., description="Creation timestamp.")


class DocumentMetadataUpsertRequest(BaseModel):
    document_id: str = Field(..., description="Document id (external or internal).")
    filename: str = Field(..., description="Original filename.")
    content_type: str = Field(..., description="MIME type.")
    size_bytes: int = Field(..., ge=0, description="Size in bytes.")
    tags: list[str] = Field(default_factory=list, description="User-defined tags.")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata.")


class InspectionStubCreateRequest(BaseModel):
    application_id: str = Field(..., description="Application id to inspect.")
    location_text: Optional[str] = Field(default=None, description="Location description (stub).")
    scheduled_at: Optional[datetime] = Field(default=None, description="When inspection is scheduled (stub).")


class TicketCreateRequest(BaseModel):
    subject: str = Field(..., description="Ticket subject.")
    description: str = Field(..., description="Ticket description.")
    category: Optional[str] = Field(default=None, description="Ticket category.")
    priority: str = Field(default="normal", description="Priority: low|normal|high|urgent.")


class PaymentInitRequest(BaseModel):
    reference_type: str = Field(..., description="What is being paid for: application|invoice|other.")
    reference_id: str = Field(..., description="Reference id for the payable item.")
    amount_paise: int = Field(..., ge=0, description="Amount in smallest currency unit (paise).")
    currency: str = Field(default="INR", description="Currency code.")
    return_url: Optional[str] = Field(default=None, description="Return URL after payment (stub).")
