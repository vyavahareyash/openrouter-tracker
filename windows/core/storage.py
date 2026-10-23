"""Windows SharedStorage using DPAPI encryption and atomic JSON storage."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List, Optional

from windows.core.models import TrackedKey, WidgetPayload

try:
    import win32crypt
    HAS_DPAPI = True
except ImportError:
    HAS_DPAPI = False


class SharedStorage:
    KEYS_META_FILE = "keys_meta.json"
    WIDGET_PAYLOAD_FILE = "openrouter_payload.json"
    SETTINGS_FILE = "settings.json"

    custom_storage_directory: Optional[Path] = None

    @classmethod
    def get_storage_directory(cls) -> Path:
        if cls.custom_storage_directory is not None:
            cls.custom_storage_directory.mkdir(parents=True, exist_ok=True)
            return cls.custom_storage_directory

        # Try %APPDATA%\OpenRouterTracker first
        candidate_dirs = []
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidate_dirs.append(Path(appdata) / "OpenRouterTracker")
        
        # User home directory fallback
        candidate_dirs.append(Path.home() / ".openrouter_tracker")

        # Local workspace / current directory fallback
        candidate_dirs.append(Path.cwd() / ".openrouter_tracker")

        for candidate in candidate_dirs:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                # Verify write access with a dummy test
                test_file = candidate / ".write_test"
                test_file.write_text("ok", encoding="utf-8")
                test_file.unlink()
                return candidate
            except (PermissionError, OSError):
                continue

        # Ultimate fallback to current directory
        fallback = Path.cwd() / ".openrouter_tracker"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    @classmethod
    def _keys_meta_file(cls) -> Path:
        return cls.get_storage_directory() / cls.KEYS_META_FILE

    @classmethod
    def _widget_payload_file(cls) -> Path:
        return cls.get_storage_directory() / cls.WIDGET_PAYLOAD_FILE

    @classmethod
    def _settings_file(cls) -> Path:
        return cls.get_storage_directory() / cls.SETTINGS_FILE

    @classmethod
    def _payload_file(cls, key_id: str) -> Path:
        return cls.get_storage_directory() / f"payload_{key_id}.json"

    @classmethod
    def _secret_file(cls, key_id: str) -> Path:
        return cls.get_storage_directory() / f"secret_{key_id}.dat"

    # MARK: - Multi-Key Management

    @classmethod
    def load_all_keys(cls) -> List[TrackedKey]:
        file_path = cls._keys_meta_file()
        if not file_path.exists():
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [TrackedKey.from_dict(item) for item in data]
        except Exception:
            return []
        return []

    @classmethod
    def save_keys_meta(cls, keys: List[TrackedKey]) -> None:
        file_path = cls._keys_meta_file()
        temp_path = file_path.with_suffix(".tmp")
        data = [key.to_dict() for key in keys]
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_path.replace(file_path)

    @classmethod
    def add_key(cls, custom_label: str, api_key: str, is_widget_key: bool = False) -> TrackedKey:
        keys = cls.load_all_keys()
        should_be_widget = is_widget_key or len(keys) == 0

        if should_be_widget:
            for k in keys:
                k.is_widget_key = False

        label = custom_label.strip()
        if not label:
            label = f"API Key {len(keys) + 1}"

        new_key = TrackedKey(
            custom_label=label,
            key_masked=TrackedKey.mask(api_key),
            is_widget_key=should_be_widget,
        )

        cls.save_raw_api_key(api_key, new_key.id)
        keys.append(new_key)
        cls.save_keys_meta(keys)
        return new_key

    @classmethod
    def update_key(cls, key: TrackedKey) -> None:
        keys = cls.load_all_keys()
        target_idx = next((i for i, k in enumerate(keys) if k.id == key.id), None)
        if target_idx is None:
            return

        if key.is_widget_key:
            for k in keys:
                k.is_widget_key = False

        keys[target_idx] = key
        cls.save_keys_meta(keys)

    @classmethod
    def delete_key(cls, key_id: str) -> None:
        keys = cls.load_all_keys()
        target_idx = next((i for i, k in enumerate(keys) if k.id == key_id), None)
        if target_idx is None:
            return

        was_widget = keys[target_idx].is_widget_key
        del keys[target_idx]

        # Delete secrets and cached payloads
        secret_file = cls._secret_file(key_id)
        if secret_file.exists():
            try:
                secret_file.unlink()
            except OSError:
                pass

        payload_file = cls._payload_file(key_id)
        if payload_file.exists():
            try:
                payload_file.unlink()
            except OSError:
                pass

        if not keys:
            cls.save_widget_payload(WidgetPayload.empty())
        elif was_widget:
            keys[0].is_widget_key = True
            cached_p = cls.get_payload(keys[0].id)
            if cached_p:
                cls.save_widget_payload(cached_p)

        cls.save_keys_meta(keys)

    @classmethod
    def set_widget_key(cls, key_id: str) -> None:
        keys = cls.load_all_keys()
        for k in keys:
            k.is_widget_key = (k.id == key_id)
        cls.save_keys_meta(keys)

        payload = cls.get_payload(key_id)
        if payload:
            cls.save_widget_payload(payload)

    @classmethod
    def get_widget_key(cls) -> Optional[TrackedKey]:
        keys = cls.load_all_keys()
        for k in keys:
            if k.is_widget_key:
                return k
        return keys[0] if keys else None

    # MARK: - Windows DPAPI Hardware-Backed Encryption

    @classmethod
    def save_raw_api_key(cls, api_key: str, key_id: str) -> None:
        clean_key = api_key.strip()
        data_bytes = clean_key.encode("utf-8")

        secret_file = cls._secret_file(key_id)
        if HAS_DPAPI:
            # DPAPI CryptProtectData binds encryption to the Windows current user
            encrypted_bytes = win32crypt.CryptProtectData(
                data_bytes, "OpenRouterTrackerKey", None, None, None, 0
            )
        else:
            # Fallback for headless/mock environments
            import base64
            encrypted_bytes = base64.b64encode(data_bytes)

        with open(secret_file, "wb") as f:
            f.write(encrypted_bytes)

    @classmethod
    def get_raw_api_key(cls, key_id: str) -> Optional[str]:
        secret_file = cls._secret_file(key_id)
        if not secret_file.exists():
            return None
        try:
            with open(secret_file, "rb") as f:
                encrypted_bytes = f.read()

            if HAS_DPAPI:
                _, decrypted_bytes = win32crypt.CryptUnprotectData(
                    encrypted_bytes, None, None, None, 0
                )
                return decrypted_bytes.decode("utf-8").strip()
            else:
                import base64
                return base64.b64decode(encrypted_bytes).decode("utf-8").strip()
        except Exception:
            return None

    # MARK: - Payload Caching

    @classmethod
    def save_payload(cls, payload: WidgetPayload, key_id: str) -> None:
        file_path = cls._payload_file(key_id)
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(payload.to_dict(), f, indent=2)
        temp_path.replace(file_path)

    @classmethod
    def get_payload(cls, key_id: str) -> Optional[WidgetPayload]:
        file_path = cls._payload_file(key_id)
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WidgetPayload.from_dict(data)
        except Exception:
            return None

    @classmethod
    def save_widget_payload(cls, payload: WidgetPayload) -> None:
        file_path = cls._widget_payload_file()
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(payload.to_dict(), f, indent=2)
        temp_path.replace(file_path)

    @classmethod
    def get_widget_payload(cls) -> Optional[WidgetPayload]:
        file_path = cls._widget_payload_file()
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return WidgetPayload.from_dict(data)
        except Exception:
            return None

    # MARK: - Settings Persistence

    @classmethod
    def get_settings(cls) -> dict:
        file_path = cls._settings_file()
        if not file_path.exists():
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def get_setting(cls, key: str, default: Any = None) -> Any:
        return cls.get_settings().get(key, default)

    @classmethod
    def set_setting(cls, key: str, value: Any) -> None:
        settings = cls.get_settings()
        settings[key] = value
        file_path = cls._settings_file()
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        temp_path.replace(file_path)
