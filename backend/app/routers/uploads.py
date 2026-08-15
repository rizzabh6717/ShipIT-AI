import os
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_session
from app.models.user import User
from app.services.delivery_request_service import DeliveryRequestService
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/photos", tags=["Uploads"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

upload_root = Path(settings.upload_dir)
upload_root.mkdir(parents=True, exist_ok=True)


async def _save_upload(file: UploadFile, folder: str) -> str:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, or WebP images are allowed",
        )
    target_dir = upload_root / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload").name
    filename = f"{folder}-{safe_name}"
    dest = target_dir / filename
    async with aiofiles.open(dest, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)
    return f"/uploads/{folder}/{filename}"


@router.post("/upload-sender-photo")
async def upload_sender_photo(
    file: UploadFile = File(...),
    _user: User = Depends(get_current_user),
):
    """Upload a photo for a parcel. Returns the public URL path."""
    url = await _save_upload(file, "parcel-photos")
    return {"success": True, "photoUrl": url, "filename": file.filename}


@router.post("/delivery-proof")
async def upload_delivery_proof(
    file: UploadFile = File(...),
    delivery_id: str = "",
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload proof-of-delivery and attach it to the delivery."""
    if not delivery_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="delivery_id is required",
        )
    delivery = await DeliveryService.get_by_public_id(session, delivery_id)
    if delivery is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found"
        )
    if delivery.driver.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your delivery"
        )
    url = await _save_upload(file, "proofs")
    await DeliveryService.set_proof(session, delivery, url)
    return {
        "success": True,
        "proofImageUrl": url,
        "deliveryId": delivery.public_id,
    }


@router.post("/delivery-request-proof")
async def upload_request_proof(
    file: UploadFile = File(...),
    request_id: str = "",
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Upload proof-of-delivery for a sender-initiated delivery request."""
    if not request_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="request_id is required",
        )
    request = await DeliveryRequestService.get_by_public_id(session, request_id)
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    if request.driver.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your request"
        )
    url = await _save_upload(file, "proofs")
    request.proof_image_url = url
    await session.flush()
    return {
        "success": True,
        "proofImageUrl": url,
        "requestId": request.public_id,
    }
