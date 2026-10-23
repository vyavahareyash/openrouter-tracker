"""Windows System Tray Manager for OpenRouter Tracker."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from windows.core.models import OpenRouterTheme
from windows.core.storage import SharedStorage


def create_default_tray_icon() -> QIcon:
    """Create a crisp, high-DPI circular gradient icon if png is not found."""
    icon_path = Path(__file__).resolve().parent.parent.parent / "OpenRouterTrackerApp" / "AppIcon.png"
    if icon_path.exists():
        return QIcon(str(icon_path))

    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Blue circle with violet dot
    painter.setBrush(QColor(OpenRouterTheme.ELECTRIC_BLUE))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 28, 28)

    painter.setBrush(QColor(OpenRouterTheme.NEON_VIOLET))
    painter.drawEllipse(10, 10, 12, 12)
    painter.end()

    return QIcon(pixmap)


class SystemTrayManager(QObject):
    """Coordinates the Windows notification area tray icon and context menu."""

    def __init__(
        self,
        main_window: QWidget,
        desktop_widget: QWidget,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.desktop_widget = desktop_widget

        self.tray_icon = QSystemTrayIcon(create_default_tray_icon(), self)
        self.tray_icon.setToolTip("OpenRouter Tracker")
        self.tray_icon.activated.connect(self._on_tray_activated)

        self._build_menu()
        self.tray_icon.show()

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #27272A;
                color: #F4F4F5;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3B82F6;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3F3F46;
                margin: 4px 6px;
            }
        """)

        # Toggle Companion Window
        act_toggle_app = menu.addAction("🖥️ Show Companion App")
        act_toggle_app.triggered.connect(self._toggle_main_window)

        # Toggle Desktop Widget
        act_toggle_widget = menu.addAction(
            "🪟 Hide Desktop Widget" if self.desktop_widget.isVisible() else "🪟 Show Desktop Widget"
        )
        act_toggle_widget.triggered.connect(self._toggle_widget)

        menu.addSeparator()

        # Widget Size Submenu
        size_menu = menu.addMenu("📐 Widget Size")
        size_menu.setStyleSheet(menu.styleSheet())
        act_small = size_menu.addAction("Small Widget (Square)")
        act_small.triggered.connect(lambda: self.desktop_widget.set_mode("small"))
        act_medium = size_menu.addAction("Medium Widget (Wide)")
        act_medium.triggered.connect(lambda: self.desktop_widget.set_mode("medium"))

        # Refresh
        act_refresh = menu.addAction("🔄 Refresh Balance Now")
        act_refresh.triggered.connect(self.desktop_widget.trigger_refresh)

        menu.addSeparator()

        # Switch Active Key Submenu
        keys = SharedStorage.load_all_keys()
        if keys:
            key_menu = menu.addMenu("🔑 Active Key")
            key_menu.setStyleSheet(menu.styleSheet())
            for k in keys:
                prefix = "✓ " if k.is_widget_key else "   "
                act_k = key_menu.addAction(f"{prefix}{k.custom_label}")

                def select_key(key_id=k.id):
                    SharedStorage.set_widget_key(key_id)
                    self.desktop_widget.load_data()
                    self.desktop_widget.trigger_refresh()
                    if hasattr(self.main_window, "load_all_data"):
                        self.main_window.load_all_data()

                act_k.triggered.connect(select_key)

        menu.addSeparator()

        # Exit
        act_exit = menu.addAction("🚪 Exit OpenRouter Tracker")
        from PySide6.QtWidgets import QApplication
        act_exit.triggered.connect(QApplication.instance().quit)

        self.tray_icon.setContextMenu(menu)

    def update_menu(self) -> None:
        self._build_menu()

    def _toggle_main_window(self) -> None:
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
        self._build_menu()

    def _toggle_widget(self) -> None:
        if self.desktop_widget.isVisible():
            self.desktop_widget.hide()
        else:
            self.desktop_widget.show()
            self.desktop_widget.raise_()
        self._build_menu()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self._toggle_main_window()
