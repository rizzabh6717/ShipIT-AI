from enum import Enum


class UserRole(str, Enum):
    SENDER = "sender"
    DRIVER = "driver"
    ADMIN = "admin"


class VehicleType(str, Enum):
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    VAN = "van"
    TRUCK = "truck"


class DriverStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class ParcelStatus(str, Enum):
    PENDING = "pending"
    PENDING_DRIVER_APPROVAL = "pending_driver_approval"
    MATCHED = "matched"
    ACCEPTED = "accepted"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryRequestStatus(str, Enum):
    PENDING_DRIVER_APPROVAL = "pending_driver_approval"
    REJECTED = "rejected"
    MATCHED = "matched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class ParcelSizeTier(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
