"""Unified Theme Manager supporting System, Dark, and Light themes on Windows."""

from __future__ import annotations

import winreg
from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from windows.core.models import OpenRouterTheme
from windows.core.storage import SharedStorage


class ThemeManager(QObject):
    theme_changed = Signal()

    _instance: Optional[ThemeManager] = None

    @classmethod
    def get_instance(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._mode = SharedStorage.get_setting("theme_mode", "system")

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode not in ("system", "dark", "light"):
            return
        self._mode = mode
        SharedStorage.set_setting("theme_mode", mode)
        self.theme_changed.emit()

    def sync_from_storage(self) -> bool:
        disk_mode = SharedStorage.get_setting("theme_mode", "system")
        if disk_mode != self._mode:
            self._mode = disk_mode
            self.theme_changed.emit()
            return True
        return False

    def is_dark(self) -> bool:
        if self._mode == "dark":
            return True
        if self._mode == "light":
            return False

        # System detection on Windows
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return val == 0  # 0 = Dark mode, 1 = Light mode
        except Exception:
            pass

        # Qt fallback
        app = QApplication.instance()
        if app and hasattr(app, "styleHints"):
            return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        return True

    # MARK: - Semantic Colors

    @property
    def bg_color(self) -> str:
        return "#18181B" if self.is_dark() else "#F8FAFC"

    @property
    def card_bg(self) -> str:
        return "#202024" if self.is_dark() else "#FFFFFF"

    @property
    def card_border(self) -> str:
        return "rgba(255, 255, 255, 0.10)" if self.is_dark() else "#E2E8F0"

    @property
    def sidebar_bg(self) -> str:
        return "#18181B" if self.is_dark() else "#F1F5F9"

    @property
    def sidebar_border(self) -> str:
        return "#27272A" if self.is_dark() else "#E2E8F0"

    @property
    def text_primary(self) -> str:
        return "#F4F4F5" if self.is_dark() else "#0F172A"

    @property
    def text_secondary(self) -> str:
        return "#A1A1AA" if self.is_dark() else "#64748B"

    @property
    def text_muted(self) -> str:
        return "#71717A" if self.is_dark() else "#94A3B8"

    @property
    def widget_bg_qcolor(self) -> QColor:
        return QColor("#1C1C20") if self.is_dark() else QColor("#FFFFFF")

    @property
    def widget_border_qcolor(self) -> QColor:
        return QColor(255, 255, 255, 22) if self.is_dark() else QColor(0, 0, 0, 24)

    @property
    def gauge_track_qcolor(self) -> QColor:
        return QColor(150, 150, 150, 45) if self.is_dark() else QColor(226, 232, 240, 220)

    @property
    def burn_track_qcolor(self) -> QColor:
        return QColor(255, 255, 255, 25) if self.is_dark() else QColor(0, 0, 0, 20)
