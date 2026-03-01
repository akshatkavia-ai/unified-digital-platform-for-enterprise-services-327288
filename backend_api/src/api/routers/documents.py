from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from src.api.core.db import db_conn_cursor, get_database_config
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
    description="Store/update document metadata in Postgres.",
    operation_id="documents_metadata_upsert",
)
def upsert_metadata(req: DocumentMetadataUpsertRequest, token_data=Depends(get_current_user_token_data), request: Request = None):
    """Upsert document metadata (Postgres-backed)."""
    cfg = get_database_config()
    with db_conn_cursor(cfg.dsn) as (_, cur):
        cur.execute(
            """
            INSERT INTO documents_metadata (document_id, filename, content_type, size_bytes, tags, extra, created_by_user_id)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT (document_id) DO UPDATE SET
              filename=EXCLUDED.filename,
              content_type=EXCLUDED.content_type,
              size_bytes=EXCLUDED.size_bytes,
              tags=EXCLUDED.tags,
              extra=EXCLUDED.extra,
              updated_at=NOW()
            """,
            (
                req.document_id,
                req.filename,
                req.content_type,
                req.size_bytes,
                req.tags,
                __import__("json").dumps(req.extra),
                token_data.user_id,
            ),
        )

    write_audit_log(
        actor_user_id=token_data.user_id,
        action="documents.metadata.upsert",
        entity_type="document",
        entity_id=req.document_id,
        metadata={"filename": req.filename, "content_type": req.content_type, "size_bytes": req.size_bytes, "tags": req.tags},
        request=request,
    )
    return DocumentMetadataResponse(document_id=req.document_id, status="upserted")
