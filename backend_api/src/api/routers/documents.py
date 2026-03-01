from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.api.core.security import get_current_user_token_data
from src.api.models.domain import DocumentMetadataUpsertRequest
from src.api.services.audit_service import write_audit_log

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentMetadataResponse(BaseModel):
    document_id: str = Field(..., description="Document id.")
    status: str = Field(..., description="Operation result.")


@router.post(
    "/metadata",
    response_model=DocumentMetadataResponse,
    summary="Upsert document metadata",
    description="Store/update document metadata (stub boundary, no storage backend yet).",
    operation_id="documents_metadata_upsert",
)
def upsert_metadata(req: DocumentMetadataUpsertRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Upsert document metadata (stub)."""
    write_audit_log(
        actor_user_id=token_data.user_id,
        action="documents.metadata.upsert",
        entity_type="document",
        entity_id=req.document_id,
        metadata={"filename": req.filename, "content_type": req.content_type, "size_bytes": req.size_bytes, "tags": req.tags},
        request=request,
    )
    return DocumentMetadataResponse(document_id=req.document_id, status="accepted")
