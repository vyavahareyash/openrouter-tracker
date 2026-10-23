"""Core domain data models and unified design tokens for OpenRouter Tracker Windows."""

from __future__ import annotations

import datetime
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TrackedKey:
    custom_label: str
    key_masked: str
    is_widget_key: bool = False
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    @staticmethod
    def mask(key: str) -> str:
        trimmed = key.strip()
        if len(trimmed) <= 12:
            return "••••••••"
        prefix = trimmed[:8]
        suffix = trimmed[-4:]
        return f"{prefix}...{suffix}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrackedKey:
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            custom_label=data.get("custom_label") or data.get("customLabel", "API Key"),
            key_masked=data.get("key_masked") or data.get("keyMasked", "••••••••"),
            is_widget_key=data.get("is_widget_key", data.get("isWidgetKey", False)),
            created_at=data.get(
                "created_at",
                data.get("createdAt", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            ),
        )


@dataclass
class WidgetPayload:
    key_label: str = "Unknown"
    custom_nickname: str = "No Key"
    key_masked: str = "None"
    key_usage: float = 0.0
    key_limit: Optional[float] = None
    key_remaining: Optional[float] = None
    usage_daily: Optional[float] = None
    usage_weekly: Optional[float] = None
    usage_monthly: Optional[float] = None
    total_credits: float = 0.0
    total_usage: float = 0.0
    total_balance: float = 0.0
    is_free_tier: bool = False
    last_updated: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    error_message: Optional[str] = None

    @property
    def usage_percent(self) -> float:
        if self.key_limit and self.key_limit > 0:
            return min(1.0, max(0.0, self.key_usage / self.key_limit))
        return 0.0

    @property
    def account_burn_percent(self) -> float:
        if self.total_credits > 0:
            return min(1.0, max(0.0, self.total_usage / self.total_credits))
        return 0.0

    @property
    def is_low_balance(self) -> bool:
        if self.key_remaining is not None and self.key_remaining <= 5.0:
            return True
        if self.total_balance <= 5.0 and self.total_credits > 0:
            return True
        if self.usage_percent >= 0.85:
            return True
        return False

    @property
    def is_critical_balance(self) -> bool:
        if self.key_remaining is not None and self.key_remaining <= 2.0:
            return True
        if self.total_balance <= 2.0 and self.total_credits > 0:
            return True
        if self.usage_percent >= 0.95:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WidgetPayload:
        return cls(
            key_label=data.get("key_label") or data.get("keyLabel", "Unknown"),
            custom_nickname=data.get("custom_nickname") or data.get("customNickname", "Key"),
            key_masked=data.get("key_masked") or data.get("keyMasked", "••••"),
            key_usage=float(data.get("key_usage", data.get("keyUsage", 0.0)) or 0.0),
            key_limit=float(data["key_limit"]) if data.get("key_limit") is not None else (
                float(data["keyLimit"]) if data.get("keyLimit") is not None else None
            ),
            key_remaining=float(data["key_remaining"]) if data.get("key_remaining") is not None else (
                float(data["keyRemaining"]) if data.get("keyRemaining") is not None else None
            ),
            usage_daily=float(data["usage_daily"]) if data.get("usage_daily") is not None else (
                float(data["usageDaily"]) if data.get("usageDaily") is not None else None
            ),
            usage_weekly=float(data["usage_weekly"]) if data.get("usage_weekly") is not None else (
                float(data["usageWeekly"]) if data.get("usageWeekly") is not None else None
            ),
            usage_monthly=float(data["usage_monthly"]) if data.get("usage_monthly") is not None else (
                float(data["usageMonthly"]) if data.get("usageMonthly") is not None else None
            ),
            total_credits=float(data.get("total_credits", data.get("totalCredits", 0.0)) or 0.0),
            total_usage=float(data.get("total_usage", data.get("totalUsage", 0.0)) or 0.0),
            total_balance=float(data.get("total_balance", data.get("totalBalance", 0.0)) or 0.0),
            is_free_tier=bool(data.get("is_free_tier", data.get("isFreeTier", False))),
            last_updated=data.get(
                "last_updated",
                data.get("lastUpdated", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            ),
            error_message=data.get("error_message") or data.get("errorMessage"),
        )

    @classmethod
    def placeholder(cls) -> WidgetPayload:
        return cls(
            key_label="sk-or-v1-...",
            custom_nickname="Default Key",
            key_masked="sk-or-v1-...59f",
            key_usage=3.46,
            key_limit=5.0,
            key_remaining=1.54,
            usage_daily=0.85,
            usage_weekly=2.10,
            usage_monthly=3.46,
            total_credits=605.0,
            total_usage=133.90,
            total_balance=471.10,
            is_free_tier=False,
            last_updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            error_message=None,
        )

    @classmethod
    def empty(cls) -> WidgetPayload:
        return cls(
            key_label="Not Configured",
            custom_nickname="No Key",
            key_masked="None",
            key_usage=0.0,
            key_limit=None,
            key_remaining=None,
            usage_daily=None,
            usage_weekly=None,
            usage_monthly=None,
            total_credits=0.0,
            total_usage=0.0,
            total_balance=0.0,
            is_free_tier=False,
            last_updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            error_message="API key not configured",
        )


class OpenRouterTheme:
    """Unified design tokens mirroring macOS OpenRouterTheme."""

    ELECTRIC_BLUE = "#3B82F6"
    NEON_VIOLET = "#A855F7"
    EMERALD_GREEN = "#10B981"
    AMBER_WARNING = "#F59E0B"
    CORAL_RED = "#EF4444"

    # Dark Mode Palette
    DARK_BG = "#18181B"          # Zinc 900
    DARK_CARD = "#27272A"        # Zinc 800
    DARK_CARD_HOVER = "#3F3F46"  # Zinc 700
    DARK_BORDER = "#3F3F46"
    DARK_TEXT_PRIMARY = "#F4F4F5"
    DARK_TEXT_SECONDARY = "#A1A1AA"
    DARK_TEXT_MUTED = "#71717A"

    # Light Mode Palette
    LIGHT_BG = "#F8FAFC"
    LIGHT_CARD = "#FFFFFF"
    LIGHT_CARD_HOVER = "#F1F5F9"
    LIGHT_BORDER = "#E2E8F0"
    LIGHT_TEXT_PRIMARY = "#0F172A"
    LIGHT_TEXT_SECONDARY = "#64748B"
    LIGHT_TEXT_MUTED = "#94A3B8"

    @classmethod
    def get_gauge_color(cls, usage_percent: float) -> str:
        if usage_percent > 0.90:
            return cls.CORAL_RED
        if usage_percent > 0.75:
            return cls.AMBER_WARNING
        return cls.ELECTRIC_BLUE
