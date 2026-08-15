from app.schemas.ai import (
    BudgetRecommend,
    BudgetRecommendRequest,
    MatchRequest,
    MatchResponse,
    MatchResult,
    RouteEmbedRequest,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterResponse,
    TokenResponse,
    UserExistsResponse,
)
from app.schemas.delivery import (
    DeliveryAcceptResponse,
    DeliveryRead,
    DeliveryStatusResponse,
)
from app.schemas.delivery_request import (
    DeliveryProofRequest,
    DeliveryRequestCreate,
    DeliveryRequestRead,
    DeliveryRequestRespond,
    DeliveryRequestResponse,
    FeedbackCreate,
    FeedbackRead,
    FeedbackResponse,
)
from app.schemas.driver import (
    DriverAvailabilityUpdate,
    DriverCreate,
    DriverRead,
    DriverStats,
    DriverUpdate,
)
from app.schemas.parcel import ParcelCreate, ParcelRead, ParcelUpdate, ParcelWithMatches
from app.schemas.route import RouteCreate, RouteEmbedResponse, RouteList, RouteRead
from app.schemas.user import DriverRegister, SenderRegister, UserCreate, UserRead, UserUpdate

__all__ = [
    "BudgetRecommend",
    "BudgetRecommendRequest",
    "DeliveryAcceptResponse",
    "DeliveryProofRequest",
    "DeliveryRead",
    "DeliveryRequestCreate",
    "DeliveryRequestRead",
    "DeliveryRequestRespond",
    "DeliveryRequestResponse",
    "DeliveryStatusResponse",
    "DriverAvailabilityUpdate",
    "DriverRegister",
    "DriverCreate",
    "DriverRead",
    "DriverStats",
    "DriverUpdate",
    "FeedbackCreate",
    "FeedbackRead",
    "FeedbackResponse",
    "LoginRequest",
    "MatchRequest",
    "MatchResponse",
    "MatchResult",
    "ParcelCreate",
    "ParcelRead",
    "ParcelUpdate",
    "ParcelWithMatches",
    "RegisterResponse",
    "RouteCreate",
    "RouteEmbedRequest",
    "RouteEmbedResponse",
    "RouteList",
    "RouteRead",
    "SenderRegister",
    "TokenResponse",
    "UserCreate",
    "UserExistsResponse",
    "UserRead",
    "UserUpdate",
]
