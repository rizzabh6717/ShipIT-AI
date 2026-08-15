"""pgvector similarity search over driver routes."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route import Route


@dataclass
class RouteHit:
    route: Route
    distance: float

    @property
    def similarity(self) -> float:
        """Cosine distance -> similarity (1 = identical)."""
        return max(0.0, 1.0 - self.distance)


async def search_routes_by_embedding(
    session: AsyncSession,
    embedding: list[float],
    top_k: int = 10,
) -> list[RouteHit]:
    """Return the nearest active routes by cosine distance using pgvector."""
    distance = Route.route_embedding.cosine_distance(embedding).label("distance")
    query = (
        select(Route, distance)
        .where(Route.is_active.is_(True), Route.route_embedding.is_not(None))
        .order_by(distance, Route.id)
        .limit(top_k)
    )
    rows = (await session.execute(query)).all()
    return [RouteHit(route=row[0], distance=float(row[1])) for row in rows]


async def search_routes_fallback(
    session: AsyncSession,
    origin: str,
    destination: str,
    top_k: int = 10,
) -> list[RouteHit]:
    """Token-overlap fallback when no embeddings are stored yet."""
    from app.utils.geo import location_overlap

    query = select(Route).where(Route.is_active.is_(True)).order_by(Route.id).limit(500)
    routes = (await session.scalars(query)).all()

    def _score(route: Route) -> float:
        return (
            location_overlap(route.origin, origin)
            + location_overlap(route.destination, destination)
        ) / 2.0

    ranked = sorted(routes, key=_score, reverse=True)[:top_k]
    return [RouteHit(route=r, distance=1.0 - _score(r)) for r in ranked]
