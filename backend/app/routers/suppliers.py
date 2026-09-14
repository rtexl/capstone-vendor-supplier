import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import (
    AuditEvent,
    Document,
    DocumentType,
    ProcessingStatus,
    Supplier,
    SupplierStatus,
)
from app.schemas import (
    SupplierCreate,
    SupplierDetail,
    SupplierSummary,
    WorkflowTransitionResponse,
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _get_supplier(db: Session, supplier_id: uuid.UUID) -> Supplier:
    supplier = db.scalar(
        select(Supplier)
        .where(Supplier.id == supplier_id)
        .options(selectinload(Supplier.documents))
    )
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier was not found.")
    return supplier


def _ensure_complete_documents(supplier: Supplier) -> None:
    ready_types = {
        document.document_type
        for document in supplier.documents
        if document.processing_status == ProcessingStatus.READY
    }
    missing = sorted(item.value for item in set(DocumentType) - ready_types)
    if missing:
        raise HTTPException(
            status_code=409,
            detail=f"Ready documents are required for: {', '.join(missing)}.",
        )


def _document_snapshot(supplier: Supplier) -> list[dict[str, str]]:
    return [
        {
            "document_id": str(document.id),
            "document_type": document.document_type.value,
            "filename": document.filename,
        }
        for document in sorted(
            supplier.documents, key=lambda item: item.document_type.value
        )
    ]


@router.post("", response_model=SupplierSummary, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)) -> SupplierSummary:
    supplier = Supplier(
        name=payload.name.strip(),
        country=payload.country.strip() if payload.country else None,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
    )
    db.add(supplier)
    db.flush()
    db.add(
        AuditEvent(
            supplier_id=supplier.id,
            action="supplier.created",
            entity_type="supplier",
            entity_id=str(supplier.id),
            details={"name": supplier.name},
        )
    )
    db.commit()
    db.refresh(supplier)
    return SupplierSummary.model_validate(supplier)


@router.get("", response_model=list[SupplierSummary])
def list_suppliers(db: Session = Depends(get_db)) -> list[SupplierSummary]:
    statement = (
        select(Supplier, func.count(Document.id).label("document_count"))
        .outerjoin(Document)
        .group_by(Supplier.id)
        .order_by(Supplier.created_at.desc())
    )
    return [
        SupplierSummary(
            **SupplierSummary.model_validate(supplier).model_dump(exclude={"document_count"}),
            document_count=count,
        )
        for supplier, count in db.execute(statement).all()
    ]


@router.get("/{supplier_id}", response_model=SupplierDetail)
def get_supplier(supplier_id: uuid.UUID, db: Session = Depends(get_db)) -> SupplierDetail:
    statement = (
        select(Supplier)
        .where(Supplier.id == supplier_id)
        .options(
            selectinload(Supplier.documents),
            selectinload(Supplier.audit_events),
            selectinload(Supplier.extracted_fields),
            selectinload(Supplier.ai_runs),
            selectinload(Supplier.compliance_results),
        )
    )
    supplier = db.execute(statement).scalar_one_or_none()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier was not found.")

    supplier.documents.sort(key=lambda item: item.created_at, reverse=True)
    supplier.audit_events.sort(key=lambda item: item.created_at, reverse=True)
    supplier.extracted_fields.sort(
        key=lambda item: (item.field_name, item.created_at), reverse=False
    )
    supplier.ai_runs.sort(key=lambda item: item.created_at, reverse=True)
    supplier.compliance_results.sort(key=lambda item: item.rule_code)
    return SupplierDetail(
        **SupplierSummary.model_validate(supplier).model_dump(exclude={"document_count"}),
        document_count=len(supplier.documents),
        documents=supplier.documents,
        audit_events=supplier.audit_events,
        extracted_fields=supplier.extracted_fields,
        ai_runs=supplier.ai_runs[:10],
        compliance_results=supplier.compliance_results,
    )


@router.post("/{supplier_id}/submit", response_model=WorkflowTransitionResponse)
def submit_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> WorkflowTransitionResponse:
    supplier = _get_supplier(db, supplier_id)
    if supplier.status != SupplierStatus.NEW:
        raise HTTPException(
            status_code=409, detail="Only a new supplier case can be submitted."
        )
    _ensure_complete_documents(supplier)
    supplier.status = SupplierStatus.SUBMITTED
    supplier.review_round = 1
    db.add(
        AuditEvent(
            supplier_id=supplier.id,
            action="supplier.submitted",
            entity_type="supplier",
            entity_id=str(supplier.id),
            details={
                "review_round": supplier.review_round,
                "documents": _document_snapshot(supplier),
            },
        )
    )
    db.commit()
    return WorkflowTransitionResponse(
        supplier_id=supplier.id,
        status=supplier.status,
        message="Supplier case submitted for review.",
        review_round=supplier.review_round,
    )


@router.post("/{supplier_id}/resubmit", response_model=WorkflowTransitionResponse)
def resubmit_supplier(
    supplier_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> WorkflowTransitionResponse:
    supplier = _get_supplier(db, supplier_id)
    if supplier.status != SupplierStatus.CHANGES_REQUESTED:
        raise HTTPException(
            status_code=409,
            detail="This supplier case is not awaiting changes.",
        )
    _ensure_complete_documents(supplier)
    current_ids = {str(document.id) for document in supplier.documents}
    requested_ids = {
        item.get("document_id")
        for item in (supplier.change_request or {}).get("documents", [])
    }
    if current_ids & requested_ids:
        raise HTTPException(
            status_code=409,
            detail="Replace every document flagged by the reviewer before resubmitting.",
        )
    supplier.status = SupplierStatus.RESUBMITTED
    supplier.review_round += 1
    db.add(
        AuditEvent(
            supplier_id=supplier.id,
            action="supplier.resubmitted",
            entity_type="supplier",
            entity_id=str(supplier.id),
            details={
                "review_round": supplier.review_round,
                "documents": _document_snapshot(supplier),
                "addressed_change_request": supplier.change_request,
            },
        )
    )
    db.commit()
    return WorkflowTransitionResponse(
        supplier_id=supplier.id,
        status=supplier.status,
        message="Updated documents resubmitted for review.",
        review_round=supplier.review_round,
    )
