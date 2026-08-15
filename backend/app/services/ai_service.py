"""Parcel text representation for embedding, plus provider info."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.parcel import Parcel
from app.models.route import Route
from app.services.route_service import RouteService


def parcel_to_text(parcel: Parcel) -> str:
    """Normalized text representation of a parcel, used as the query embedding."""
    parts = [
        f"Shipment from {parcel.pickup_location} to {parcel.drop_location}",
        f"Item: {parcel.item_description}",
        f"Weight: {parcel.weight} kg",
        f"Size tier: {parcel.size_tier.value}",
        f"Budget: {parcel.budget:.2f}",
    ]
    if parcel.deadline:
        parts.append(f"Deadline: {parcel.deadline.isoformat()}")
    return "\n".join(parts)


class AIService:
    """Route embedding generation and model/provider introspection."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def embed_route(self, route: Route) -> Route:
        """Generate and persist the pgvector embedding for a route."""
        return await RouteService.embed(self.session, route)

    async def get_route(self, route_id: int) -> Route | None:
        return await RouteService.get(self.session, route_id)

    async def create_and_embed_route(self, driver_id: int, data) -> Route:
        route = await RouteService.create(self.session, driver_id, data)
        return await self.embed_route(route)

    @staticmethod
    def provider_info() -> dict:
        return {
            "embedding_provider": settings.embedding_provider,
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "ranked_by": "ai" if settings.llm_api_key and settings.llm_provider in {"openrouter", "openai"} else "heuristic",
        }

    async def parcel_by_public_id(self, public_id: str) -> Parcel | None:
        from app.services.parcel_service import ParcelService

        return await ParcelService.get_by_public_id(self.session, public_id)
