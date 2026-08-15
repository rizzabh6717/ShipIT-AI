from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.dependencies import get_current_user, get_session
from app.models.match import Match
from app.models.user import User
from app.services.ai_service import AIService
from app.services.matching_service import MatchingService
from app.services.parcel_service import ParcelService
from app.services.pricing_service import recommend

router = APIRouter(prefix="/ai", tags=["AI Matching"])


@router.post("/match", response_model=schemas.MatchResponse)
async def match_parcel(
    data: schemas.MatchRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Run the AI matching pipeline for a parcel.

    Body: {"parcel_id": "P123"}
    Returns ranked, explainable driver matches (LLM or heuristic).
    """
    parcel = await ParcelService.get_by_public_id(session, data.parcel_id)
    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found"
        )
    service = MatchingService(session)
    return await service.match_parcel(parcel)


@router.get("/matches/{parcel_id}", response_model=schemas.MatchResponse)
async def get_matches(
    parcel_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the most recent persisted matches for a parcel."""
    parcel = await ParcelService.get_by_public_id(session, parcel_id)
    if parcel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found"
        )
    rows = (
        await session.scalars(
            select(Match)
            .where(Match.parcel_id == parcel.id)
            .order_by(Match.match_score.desc())
        )
    ).all()
    return schemas.MatchResponse(
        parcel_id=parcel.public_id,
        matches=[
            schemas.MatchResult(
                driver_id=m.driver.public_id if m.driver else "",
                score=m.match_score,
                eta=m.eta or "",
                reason=(m.explanation or "").split("\n"),
            )
            for m in rows
        ],
        ranked_by="ai",
    )


@router.post("/budget-recommend", response_model=schemas.BudgetRecommend)
async def budget_recommend(
    data: schemas.BudgetRecommendRequest,
    _user: User = Depends(get_current_user),
):
    """Suggest a starting budget for a parcel based on route, weight, dimensions."""
    return recommend(
        data.pickup_location,
        data.drop_location,
        data.weight,
        data.dimensions,
        data.size_tier,
    )


@router.get("/status")
async def ai_status(
    _user: User = Depends(get_current_user),
):
    """Report which embedding/LLM providers are configured."""
    return {"status": "ok", **AIService.provider_info()}
