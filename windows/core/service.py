"""Network client for OpenRouter API querying /auth/key and /credits."""

from __future__ import annotations

import datetime
import json
import urllib.error
import urllib.request
from typing import Optional

from windows.core.models import TrackedKey, WidgetPayload
from windows.core.storage import SharedStorage


class OpenRouterService:
    USER_AGENT = "OpenRouterTracker/2.0 (Windows)"
    AUTH_KEY_URL = "https://openrouter.ai/api/v1/auth/key"
    CREDITS_URL = "https://openrouter.ai/api/v1/credits"
    TIMEOUT_SECONDS = 10

    @classmethod
    def fetch_data(cls, api_key: str, custom_nickname: str) -> WidgetPayload:
        clean_key = api_key.strip()
        if not clean_key:
            return WidgetPayload.empty()

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        payload = WidgetPayload(
            key_label="Unknown",
            custom_nickname=custom_nickname or "Key",
            key_masked=TrackedKey.mask(clean_key),
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
            last_updated=now_iso,
            error_message=None,
        )

        # 1. Fetch Key Metrics & Limits
        try:
            req = urllib.request.Request(
                cls.AUTH_KEY_URL,
                headers={
                    "Authorization": f"Bearer {clean_key}",
                    "User-Agent": cls.USER_AGENT,
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=cls.TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            key_data = data.get("data") or {}
            payload.key_label = key_data.get("label") or "Key"
            payload.key_usage = float(key_data.get("usage") or 0.0)
            
            raw_limit = key_data.get("limit")
            if raw_limit is not None:
                payload.key_limit = float(raw_limit)
                payload.key_remaining = max(0.0, payload.key_limit - payload.key_usage)
            else:
                payload.key_limit = None
                payload.key_remaining = None

            payload.usage_daily = float(key_data["usage_daily"]) if key_data.get("usage_daily") is not None else None
            payload.usage_weekly = float(key_data["usage_weekly"]) if key_data.get("usage_weekly") is not None else None
            payload.usage_monthly = float(key_data["usage_monthly"]) if key_data.get("usage_monthly") is not None else None
            payload.is_free_tier = bool(key_data.get("is_free_tier", False))

        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = err_json.get("error", {}).get("message") or err_body[:80]
            except Exception:
                err_msg = f"HTTP {e.code}"
            payload.error_message = f"Auth failed: {err_msg}"
            return payload
        except Exception as e:
            payload.error_message = f"Network err: {e}"
            return payload

        # 2. Fetch Account Credits & Balance (non-fatal if it fails)
        try:
            credits_req = urllib.request.Request(
                cls.CREDITS_URL,
                headers={
                    "Authorization": f"Bearer {clean_key}",
                    "User-Agent": cls.USER_AGENT,
                },
                method="GET",
            )
            with urllib.request.urlopen(credits_req, timeout=cls.TIMEOUT_SECONDS) as resp:
                if resp.status == 200:
                    c_data = json.loads(resp.read().decode("utf-8"))
                    cd = c_data.get("data") or {}
                    total = float(cd.get("total_credits") or 0.0)
                    used = float(cd.get("total_usage") or 0.0)
                    payload.total_credits = total
                    payload.total_usage = used
                    payload.total_balance = max(0.0, total - used)
        except Exception:
            # Account credits query failure is non-fatal for individual key stats
            pass

        return payload

    @classmethod
    def refresh_key(cls, key: TrackedKey) -> WidgetPayload:
        raw_key = SharedStorage.get_raw_api_key(key.id)
        if not raw_key:
            empty = WidgetPayload.empty()
            empty.custom_nickname = key.custom_label
            empty.key_masked = key.key_masked
            return empty

        payload = cls.fetch_data(raw_key, custom_nickname=key.custom_label)
        SharedStorage.save_payload(payload, key.id)

        if key.is_widget_key:
            SharedStorage.save_widget_payload(payload)

        return payload

    @classmethod
    def refresh_widget_key(cls) -> WidgetPayload:
        widget_key = SharedStorage.get_widget_key()
        if not widget_key:
            return WidgetPayload.empty()
        return cls.refresh_key(widget_key)
