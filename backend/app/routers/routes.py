from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.dependencies import get_current_user, get_session
from app.models.user import User
from app.services.ai_service import AIService
from app.services.driver_service import DriverService
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.post("", response_model=schemas.RouteRead, status_code=status.HTTP_201_CREATED)
async def create_route(
    data: schemas.RouteCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Register a planned route and immediately generate its embedding."""
    driver = await DriverService.ensure_profile(session, user)
    route = await RouteService.create(session, driver.id, data)
    try:
        await RouteService.embed(session, route)
    except Exception:
        # Embedding failure should not block route creation; the driver can
        # re-trigger embedding via POST /routes/me/embed.
        pass
    item = schemas.RouteRead.model_validate(route)
    item.has_embedding = route.route_embedding is not None
    return item


@router.get("/me", response_model=schemas.RouteList)
async def my_routes(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return the authenticated driver's routes."""
    driver = await DriverService.ensure_profile(session, user)
    routes = await RouteService.list_for_driver(session, driver.id)
    items = []
    for r in routes:
        item = schemas.RouteRead.model_validate(r)
        item.has_embedding = r.route_embedding is not None
        items.append(item)
    return schemas.RouteList(routes=items, total=len(items))


@router.post("/me/embed", response_model=schemas.RouteEmbedResponse)
async def embed_my_active_routes(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """(Re)generate embeddings for all of the driver's active routes."""
    driver = await DriverService.ensure_profile(session, user)
    ai = AIService(session)
    routes = await RouteService.list_for_driver(session, driver.id, active_only=True)
    if not routes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active routes to embed"
        )
    updated = []
    for route in routes:
        updated.append(await ai.embed_route(route))
    first = updated[0]
    return schemas.RouteEmbedResponse(
        route_id=first.id,
        status="embedded",
        dimensions=len(first.route_embedding) if first.route_embedding else 0,
        route_text=first.route_text or "",
    )


@router.post("/embed", response_model=schemas.RouteEmbedResponse)
async def embed_route_by_request(
    data: schemas.RouteEmbedRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Embed an existing route by id, or create+embed one on the fly."""
    driver = await DriverService.ensure_profile(session, user)
    ai = AIService(session)
    if data.route_id is not None:
        route = await ai.get_route(data.route_id)
        if route is None or route.driver_id != driver.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Route not found"
            )
        await ai.embed_route(route)
    else:
        route = await ai.create_and_embed_route(driver.id, data)
    return schemas.RouteEmbedResponse(
        route_id=route.id,
        status="embedded",
        dimensions=len(route.route_embedding) if route.route_embedding else 0,
        route_text=route.route_text or "",
    )
