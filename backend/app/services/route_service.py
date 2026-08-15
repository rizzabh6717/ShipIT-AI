from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import get_embedder
from app.models.route import Route
from app.schemas.route import RouteCreate


def build_route_text(origin: str, destination: str, waypoints: list[dict] | None = None) -> str:
    """Turn a structured route into a canonical text representation.

    Example:
      Route from Mumbai, Maharashtra to Pune, Maharashtra
      via stop 1: Thane; stop 2: Lonavala.
    """
    lines = [f"Route from {origin} to {destination}."]
    if waypoints:
        stops = []
        for i, wp in enumerate(waypoints, start=1):
            label = wp.get("label") or wp.get("city") or wp.get("address") or f"stop {i}"
            stops.append(f"{label}")
        lines.append("Via stops: " + "; ".join(stops) + ".")
    return "\n".join(lines)


class RouteService:
    """Driver route management, including embedding generation."""

    @staticmethod
    async def create(session: AsyncSession, driver_id: int, data: RouteCreate) -> Route:
        route = Route(
            driver_id=driver_id,
            origin=data.origin,
            destination=data.destination,
            waypoints=data.waypoints,
            route_text=build_route_text(data.origin, data.destination, data.waypoints),
            is_active=True,
            planned_at=data.planned_at,
        )
        session.add(route)
        await session.flush()
        return route

    @staticmethod
    async def get(session: AsyncSession, route_id: int) -> Route | None:
        return await session.get(Route, route_id)

    @staticmethod
    async def list_for_driver(session: AsyncSession, driver_id: int, active_only: bool = True) -> list[Route]:
        query = select(Route).where(Route.driver_id == driver_id)
        if active_only:
            query = query.where(Route.is_active.is_(True))
        query = query.order_by(Route.created_at.desc())
        return list((await session.scalars(query)).all())

    @staticmethod
    async def deactivate_others(session: AsyncSession, driver_id: int, keep_id: int | None = None) -> None:
        """Deactivate all of a driver's routes except the given one."""
        routes = await RouteService.list_for_driver(session, driver_id, active_only=True)
        for route in routes:
            if route.id != keep_id:
                route.is_active = False
        await session.flush()

    @staticmethod
    async def embed(session: AsyncSession, route: Route) -> Route:
        """Generate and store the pgvector embedding for a route."""
        route_text = route.route_text or build_route_text(route.origin, route.destination, route.waypoints)
        embedder = get_embedder()
        embedding = await embedder.embed([route_text])
        route.route_text = route_text
        route.route_embedding = embedding[0]
        route.planned_at = route.planned_at or datetime.now()
        await session.flush()
        return route

    @staticmethod
    async def set_active(session: AsyncSession, route: Route, active: bool) -> Route:
        route.is_active = active
        await session.flush()
        return route
