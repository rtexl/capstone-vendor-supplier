from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Document, DocumentType, ProcessingStatus, Supplier, SupplierStatus
from app.routers.review import request_supplier_changes, start_review
from app.routers.suppliers import resubmit_supplier, submit_supplier
from app.schemas import ChangesRequest, DocumentChangeRequest


def _review_case(db: Session) -> Supplier:
    supplier = Supplier(name="Workflow Test Supplier", country="India")
    db.add(supplier)
    db.flush()
    for document_type in DocumentType:
        db.add(
            Document(
                supplier_id=supplier.id,
                document_type=document_type,
                filename=f"{document_type.value}.txt",
                storage_path=str(Path("/tmp") / f"{document_type.value}.txt"),
                content_type="text/plain",
                file_size=20,
                page_count=1,
                extracted_text="Ready test document",
                processing_status=ProcessingStatus.READY,
            )
        )
    db.commit()
    return supplier


def test_supplier_can_replace_flagged_document_and_resubmit() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        supplier = _review_case(db)

        submitted = submit_supplier(supplier.id, db)
        assert submitted.status == SupplierStatus.SUBMITTED
        assert submitted.review_round == 1

        started = start_review(supplier.id, db)
        assert started.status == SupplierStatus.UNDER_REVIEW

        rejected_document = supplier.documents[0]
        requested = request_supplier_changes(
            supplier.id,
            ChangesRequest(
                documents=[
                    DocumentChangeRequest(
                        document_id=rejected_document.id,
                        reason="The certificate is expired.",
                    )
                ]
            ),
            db,
        )
        assert requested.status == SupplierStatus.CHANGES_REQUESTED

        document_type = rejected_document.document_type
        db.delete(rejected_document)
        db.commit()
        db.add(
            Document(
                supplier_id=supplier.id,
                document_type=document_type,
                filename="replacement.txt",
                storage_path="/tmp/replacement.txt",
                content_type="text/plain",
                file_size=25,
                page_count=1,
                extracted_text="Replacement test document",
                processing_status=ProcessingStatus.READY,
            )
        )
        db.commit()
        db.expire_all()

        resubmitted = resubmit_supplier(supplier.id, db)
        assert resubmitted.status == SupplierStatus.RESUBMITTED
        assert resubmitted.review_round == 2

        actions = [event.action for event in supplier.audit_events]
        assert "supplier.submitted" in actions
        assert "supplier.review_started" in actions
        assert "supplier.changes_requested" in actions
        assert "supplier.resubmitted" in actions


def test_supplier_cannot_resubmit_without_replacing_flagged_document() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        supplier = _review_case(db)
        submit_supplier(supplier.id, db)
        start_review(supplier.id, db)
        request_supplier_changes(
            supplier.id,
            ChangesRequest(
                documents=[
                    DocumentChangeRequest(
                        document_id=supplier.documents[0].id,
                        reason="A corrected document is required.",
                    )
                ]
            ),
            db,
        )

        with pytest.raises(HTTPException, match="Replace every document") as exc_info:
            resubmit_supplier(supplier.id, db)

        assert exc_info.value.status_code == 409
