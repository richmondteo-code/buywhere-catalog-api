"""Batch CSV import routes for affiliate commissions."""

import asyncio
import csv
import io
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_api_key
from app.database import get_db
from app.models.product import ApiKey
from app.models.affiliate import AffiliateCommission
from app.models.affiliate_import import AffiliateImportJob
from app.services.currency import convert_price

logger = logging.getLogger("buywhere_api")

router = APIRouter(prefix="/v1/affiliate/import", tags=["affiliate"])

CSV_COLUMNS = {"clickId", "conversionId", "productId", "commissionAmount", "commissionCurrency", "orderValue", "orderCurrency", "timestamp", "status"}


class ImportJobStatusResponse(BaseModel):
    job_id: str
    network: str
    status: str
    total_rows: int
    rows_processed: int
    rows_succeeded: int
    rows_failed: int
    error_message: Optional[str] = None
    created_at: datetime


class ImportJobListResponse(BaseModel):
    jobs: list[ImportJobStatusResponse]


def _parse_csv_row(row: dict, line_num: int) -> Optional[dict]:
    try:
        click_id = row.get("clickId", "").strip()
        if not click_id:
            return None

        commission_amount = Decimal(str(row.get("commissionAmount", "0")).strip())
        commission_currency = row.get("commissionCurrency", "SGD").strip().upper()
        order_value_str = row.get("orderValue", "").strip()
        order_value = Decimal(order_value_str) if order_value_str else None
        order_currency = row.get("orderCurrency", "").strip().upper() or None
        status_str = row.get("status", "pending").strip()
        timestamp_str = row.get("timestamp", "").strip()

        timestamp = None
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        product_id_str = row.get("productId", "").strip()
        product_id = int(product_id_str) if product_id_str and product_id_str.isdigit() else None

        conversion_id = row.get("conversionId", "").strip() or None

        return {
            "click_id": click_id,
            "conversion_id": conversion_id,
            "product_id": product_id,
            "commission_amount": commission_amount,
            "commission_currency": commission_currency,
            "order_value": order_value,
            "order_currency": order_currency,
            "timestamp": timestamp,
            "status": status_str,
        }
    except Exception as exc:
        logger.warning("Failed to parse CSV row %d: %s", line_num, exc)
        return None


async def _process_import(job_id: str, network: str, csv_content: str):
    """Background task to process CSV import."""
    from app.database import get_session_maker
    async with get_session_maker()() as db:
        try:
            result = await db.execute(select(AffiliateImportJob).where(AffiliateImportJob.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                return

            job.status = "processing"
            await db.flush()

            reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(reader)
            job.total_rows = len(rows)

            succeeded = 0
            failed = 0

            for i, row in enumerate(rows):
                parsed = _parse_csv_row(row, i + 2)
                if not parsed:
                    failed += 1
                    job.rows_failed = failed
                    job.rows_processed = succeeded + failed
                    await db.flush()
                    continue

                existing = await db.execute(
                    select(AffiliateCommission).where(AffiliateCommission.click_id == parsed["click_id"])
                )
                if existing.scalar_one_or_none():
                    failed += 1
                    job.rows_failed = failed
                    job.rows_processed = succeeded + failed
                    await db.flush()
                    continue

                commission_sgd = await convert_price(
                    parsed["commission_amount"], parsed["commission_currency"], "SGD"
                )
                order_sgd = None
                if parsed["order_value"] is not None and parsed["order_currency"]:
                    order_sgd = await convert_price(
                        parsed["order_value"], parsed["order_currency"], "SGD"
                    )

                commission = AffiliateCommission(
                    click_id=parsed["click_id"],
                    conversion_id=parsed["conversion_id"],
                    product_id=parsed["product_id"],
                    network=network,
                    commission_amount=parsed["commission_amount"],
                    commission_currency=parsed["commission_currency"],
                    commission_amount_sgd=commission_sgd,
                    order_value=parsed["order_value"],
                    order_currency=parsed["order_currency"],
                    order_value_sgd=order_sgd,
                    timestamp=parsed["timestamp"],
                    status=parsed["status"],
                    import_job_id=job_id,
                )
                db.add(commission)
                succeeded += 1
                job.rows_succeeded = succeeded
                job.rows_processed = succeeded + failed

                if (succeeded + failed) % 100 == 0:
                    await db.flush()

            await db.flush()
            job.status = "completed" if failed == 0 else "completed_with_errors"
            await db.commit()

        except Exception as exc:
            logger.exception("Import job %s failed", job_id)
            await db.rollback()
            try:
                async with get_session_maker()() as fresh_db:
                    job = await fresh_db.get(AffiliateImportJob, job_id)
                    if job:
                        job.status = "failed"
                        job.error_message = str(exc)[:500]
                        await fresh_db.commit()
            except Exception:
                pass


@router.post("/{network}", status_code=status.HTTP_202_ACCEPTED, summary="Upload CSV for affiliate commission batch import")
async def upload_affiliate_csv(
    request: Request,
    network: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> dict:
    request.state.api_key = api_key

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    try:
        csv_text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(csv_text))
    provided_columns = set(reader.fieldnames or [])

    if not CSV_COLUMNS.issubset(provided_columns):
        missing = CSV_COLUMNS - provided_columns
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(sorted(missing))}",
        )

    job_id = str(uuid.uuid4())
    job = AffiliateImportJob(
        id=job_id,
        network=network,
        status="pending",
    )
    db.add(job)
    await db.flush()

    asyncio.create_task(_process_import(job_id, network, csv_text))

    return {
        "job_id": job_id,
        "network": network,
        "status": "pending",
        "message": "Import started. Poll GET /v1/affiliate/import/{network}/status/{job_id} for progress.",
    }


@router.get("/{network}/status/{job_id}", response_model=ImportJobStatusResponse, summary="Poll import job status")
async def get_import_status(
    request: Request,
    network: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ImportJobStatusResponse:
    request.state.api_key = api_key

    result = await db.execute(
        select(AffiliateImportJob).where(
            AffiliateImportJob.id == job_id,
            AffiliateImportJob.network == network,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    return ImportJobStatusResponse(
        job_id=job.id,
        network=job.network,
        status=job.status,
        total_rows=job.total_rows or 0,
        rows_processed=job.rows_processed or 0,
        rows_succeeded=job.rows_succeeded or 0,
        rows_failed=job.rows_failed or 0,
        error_message=job.error_message,
        created_at=job.created_at,
    )


@router.get("/jobs", response_model=ImportJobListResponse, summary="List recent import jobs")
async def list_import_jobs(
    request: Request,
    network: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_current_api_key),
) -> ImportJobListResponse:
    request.state.api_key = api_key

    query = select(AffiliateImportJob).order_by(AffiliateImportJob.created_at.desc()).limit(limit)
    if network:
        query = query.where(AffiliateImportJob.network == network)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return ImportJobListResponse(
        jobs=[
            ImportJobStatusResponse(
                job_id=j.id,
                network=j.network,
                status=j.status,
                total_rows=j.total_rows or 0,
                rows_processed=j.rows_processed or 0,
                rows_succeeded=j.rows_succeeded or 0,
                rows_failed=j.rows_failed or 0,
                error_message=j.error_message,
                created_at=j.created_at,
            )
            for j in jobs
        ]
    )
