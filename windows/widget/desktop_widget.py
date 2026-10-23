"""Windows Desktop Widget with Small & Medium layouts, frameless drag, and 1-click refresh."""

from __future__ import annotations

import datetime
import threading
from typing import Callable, Optional

from PySide6.QtCore import QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from windows.core.models import OpenRouterTheme, TrackedKey, WidgetPayload
from windows.core.service import OpenRouterService
from windows.core.storage import SharedStorage
from windows.widget.radial_gauge import RadialGauge


class RefreshButton(QPushButton):
    """Tactile 1-click refresh button with subtle hover and spinning/loading state."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("🔄", parent)
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Refresh OpenRouter balance now")
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(150, 150, 150, 0.15);
                color: #A1A1AA;
                border: none;
                border-radius: 11px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.35);
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: rgba(59, 130, 246, 0.60);
            }
            QPushButton:disabled {
                color: #555555;
                background-color: transparent;
            }
        """)


class DesktopWidget(QWidget):
    """Frameless translucent desktop widget matching macOS WidgetKit."""

    refresh_completed = Signal(object)
    open_companion_requested = Signal()

    SMALL_SIZE = QSize(168, 168)
    MEDIUM_SIZE = QSize(350, 168)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._drag_pos: Optional[QPoint] = None
        self._is_refreshing: bool = False
        self.mode: str = SharedStorage.get_setting("widget_mode", "medium")
        self.pinned_to_desktop: bool = SharedStorage.get_setting("widget_pinned_to_desktop", False)
        self.always_on_top: bool = SharedStorage.get_setting("widget_always_on_top", False)

        self._init_window()
        self._init_ui()
        self.load_data()
        self.refresh_completed.connect(self._on_refresh_done)

    def _init_window(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._update_window_flags()

        # Restore geometry if saved
        saved_x = SharedStorage.get_setting("widget_x")
        saved_y = SharedStorage.get_setting("widget_y")
        if saved_x is not None and saved_y is not None:
            self.move(int(saved_x), int(saved_y))
        else:
            self.move(100, 100)

        target_size = self.MEDIUM_SIZE if self.mode == "medium" else self.SMALL_SIZE
        self.setFixedSize(target_size)

    def _update_window_flags(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        elif self.pinned_to_desktop:
            flags |= Qt.WindowType.WindowStaysOnBottomHint

        self.setWindowFlags(flags)

    def _init_ui(self) -> None:
        # Root layout with padding
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(0)

        # Container card
        self.card = QWidget(self)
        self.card.setObjectName("widgetCard")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(10, 10, 10, 10)
        self.card_layout.setSpacing(6)
        self.root_layout.addWidget(self.card)

        self._build_content()

    def _build_content(self) -> None:
        # Clear existing layout
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if self.mode == "medium":
            self._build_medium_layout()
        else:
            self._build_small_layout()

    def _build_small_layout(self) -> None:
        # Header: Nickname + Refresh
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {OpenRouterTheme.NEON_VIOLET}; font-size: 8px;")
        header.addWidget(dot)

        self.lbl_nickname = QLabel("OpenRouter")
        self.lbl_nickname.setStyleSheet("color: #F4F4F5; font-size: 11px; font-weight: bold;")
        self.lbl_nickname.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header.addWidget(self.lbl_nickname)

        self.btn_refresh = RefreshButton()
        self.btn_refresh.clicked.connect(self.trigger_refresh)
        header.addWidget(self.btn_refresh)
        self.card_layout.addLayout(header)

        # Center Gauge
        self.radial_gauge = RadialGauge(stroke_width=7.5)
        self.radial_gauge.setFixedSize(110, 110)
        gauge_container = QHBoxLayout()
        gauge_container.addStretch()
        gauge_container.addWidget(self.radial_gauge)
        gauge_container.addStretch()
        self.card_layout.addLayout(gauge_container)

    def _build_medium_layout(self) -> None:
        main_hbox = QHBoxLayout()
        main_hbox.setContentsMargins(0, 0, 0, 0)
        main_hbox.setSpacing(10)

        # Left Column: Key Specific
        left_vbox = QVBoxLayout()
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(4)

        # Key Header
        key_header = QHBoxLayout()
        key_header.setSpacing(4)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 8px;")
        key_header.addWidget(dot)

        self.lbl_nickname = QLabel("OpenRouter")
        self.lbl_nickname.setStyleSheet("color: #F4F4F5; font-size: 11px; font-weight: bold;")
        key_header.addWidget(self.lbl_nickname)
        key_header.addStretch()
        left_vbox.addLayout(key_header)

        self.lbl_masked = QLabel("••••••••")
        self.lbl_masked.setStyleSheet("color: #71717A; font-family: Consolas, monospace; font-size: 8px;")
        left_vbox.addWidget(self.lbl_masked)

        left_vbox.addSpacing(2)

        # Gauge + Spent/Limit Stats Row
        gauge_row = QHBoxLayout()
        gauge_row.setContentsMargins(0, 0, 0, 0)
        gauge_row.setSpacing(8)

        self.radial_gauge = RadialGauge(stroke_width=6.0)
        self.radial_gauge.setFixedSize(82, 82)
        gauge_row.addWidget(self.radial_gauge)

        stats_vbox = QVBoxLayout()
        stats_vbox.setContentsMargins(0, 0, 0, 0)
        stats_vbox.setSpacing(4)

        lbl_spent_title = QLabel("SPENT")
        lbl_spent_title.setStyleSheet("color: #8C8C96; font-size: 7px; font-weight: bold;")
        self.lbl_spent_val = QLabel("$0.00")
        self.lbl_spent_val.setStyleSheet(f"color: {OpenRouterTheme.NEON_VIOLET}; font-size: 11px; font-weight: bold;")

        lbl_limit_title = QLabel("LIMIT")
        lbl_limit_title.setStyleSheet("color: #8C8C96; font-size: 7px; font-weight: bold;")
        self.lbl_limit_val = QLabel("Unlimited")
        self.lbl_limit_val.setStyleSheet(f"color: {OpenRouterTheme.AMBER_WARNING}; font-size: 11px; font-weight: bold;")

        stats_vbox.addWidget(lbl_spent_title)
        stats_vbox.addWidget(self.lbl_spent_val)
        stats_vbox.addSpacing(2)
        stats_vbox.addWidget(lbl_limit_title)
        stats_vbox.addWidget(self.lbl_limit_val)
        stats_vbox.addStretch()

        gauge_row.addLayout(stats_vbox)
        left_vbox.addLayout(gauge_row)
        left_vbox.addStretch()
        main_hbox.addLayout(left_vbox, stretch=3)

        # Vertical Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet("color: rgba(255, 255, 255, 0.12);")
        main_hbox.addWidget(divider)

        # Right Column: Account Overview Card
        right_card = QWidget()
        right_card.setStyleSheet("""
            QWidget {
                background-color: rgba(59, 130, 246, 0.08);
                border: 1px solid rgba(59, 130, 246, 0.18);
                border-radius: 8px;
            }
        """)
        right_vbox = QVBoxLayout(right_card)
        right_vbox.setContentsMargins(8, 6, 8, 6)
        right_vbox.setSpacing(3)

        acct_header = QHBoxLayout()
        lbl_acct_title = QLabel("Account Total")
        lbl_acct_title.setStyleSheet("color: #A1A1AA; font-size: 9px; font-weight: 600; border: none; background: transparent;")
        acct_header.addWidget(lbl_acct_title)
        acct_header.addStretch()

        self.btn_refresh = RefreshButton()
        self.btn_refresh.clicked.connect(self.trigger_refresh)
        acct_header.addWidget(self.btn_refresh)
        right_vbox.addLayout(acct_header)

        lbl_bal_caption = QLabel("Available Balance")
        lbl_bal_caption.setStyleSheet("color: #8C8C96; font-size: 8px; border: none; background: transparent;")
        right_vbox.addWidget(lbl_bal_caption)

        self.lbl_acct_balance = QLabel("$0.00")
        self.lbl_acct_balance.setStyleSheet(f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 15px; font-weight: bold; border: none; background: transparent;")
        right_vbox.addWidget(self.lbl_acct_balance)

        # Account Burn Bar
        self.burn_bar = QWidget()
        self.burn_bar.setFixedHeight(4)
        self.burn_bar.setStyleSheet("background: transparent; border: none;")
        right_vbox.addWidget(self.burn_bar)

        burn_stats = QHBoxLayout()
        burn_stats.setContentsMargins(0, 0, 0, 0)
        self.lbl_burn_used = QLabel("Used $0")
        self.lbl_burn_used.setStyleSheet("color: #8C8C96; font-size: 7.5px; border: none; background: transparent;")
        self.lbl_burn_total = QLabel("Total $0")
        self.lbl_burn_total.setStyleSheet("color: #8C8C96; font-size: 7.5px; border: none; background: transparent;")
        burn_stats.addWidget(self.lbl_burn_used)
        burn_stats.addStretch()
        burn_stats.addWidget(self.lbl_burn_total)
        right_vbox.addLayout(burn_stats)

        right_vbox.addStretch()

        self.lbl_updated = QLabel("Updated just now")
        self.lbl_updated.setStyleSheet("color: #71717A; font-size: 7px; border: none; background: transparent;")
        self.lbl_updated.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_vbox.addWidget(self.lbl_updated)

        main_hbox.addWidget(right_card, stretch=2)
        self.card_layout.addLayout(main_hbox)

    # MARK: - Data Loading & Rendering

    def load_data(self) -> None:
        payload = SharedStorage.get_widget_payload()
        if not payload:
            widget_key = SharedStorage.get_widget_key()
            if widget_key:
                payload = SharedStorage.get_payload(widget_key.id)
            if not payload:
                payload = WidgetPayload.empty()

        self.apply_payload(payload)

    def apply_payload(self, payload: WidgetPayload) -> None:
        self.current_payload = payload
        self.lbl_nickname.setText(payload.custom_nickname or "OpenRouter")

        if hasattr(self, "radial_gauge"):
            self.radial_gauge.set_payload(payload)

        if self.mode == "medium":
            self.lbl_masked.setText(payload.key_masked or "••••")
            self.lbl_spent_val.setText(f"${payload.key_usage:.2f}")

            if payload.key_limit is not None and payload.key_limit > 0:
                self.lbl_limit_val.setText(f"${payload.key_limit:.2f}")
            else:
                self.lbl_limit_val.setText("Unlimited")

            self.lbl_acct_balance.setText(f"${payload.total_balance:.2f}")
            self.lbl_burn_used.setText(f"Used ${int(payload.total_usage)}")
            self.lbl_burn_total.setText(f"Total ${int(payload.total_credits)}")

            try:
                dt = datetime.datetime.fromisoformat(payload.last_updated)
                time_str = dt.strftime("%H:%M")
            except Exception:
                time_str = "Recent"
            self.lbl_updated.setText(f"Updated {time_str}")

        self.update()

    # MARK: - Interactive Tactile 1-Click Refresh

    def trigger_refresh(self) -> None:
        if self._is_refreshing:
            return
        self._is_refreshing = True
        if hasattr(self, "btn_refresh"):
            self.btn_refresh.setEnabled(False)
            self.btn_refresh.setText("⏳")

        def worker():
            try:
                payload = OpenRouterService.refresh_widget_key()
                self.refresh_completed.emit(payload)
            except Exception as e:
                empty = WidgetPayload.empty()
                empty.error_message = str(e)
                self.refresh_completed.emit(empty)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_refresh_done(self, payload: WidgetPayload) -> None:
        self._is_refreshing = False
        if hasattr(self, "btn_refresh"):
            self.btn_refresh.setEnabled(True)
            self.btn_refresh.setText("🔄")
        self.apply_payload(payload)

    # MARK: - Mode Switching

    def set_mode(self, mode: str) -> None:
        if mode not in ("small", "medium"):
            return
        self.mode = mode
        SharedStorage.set_setting("widget_mode", mode)
        target_size = self.MEDIUM_SIZE if mode == "medium" else self.SMALL_SIZE
        self.setFixedSize(target_size)
        self._build_content()
        self.load_data()

    # MARK: - Window Dragging & Coordinates Persistence

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = None
            SharedStorage.set_setting("widget_x", self.pos().x())
            SharedStorage.set_setting("widget_y", self.pos().y())
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # MARK: - Right-Click Context Menu

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #27272A;
                color: #F4F4F5;
                border: 1px solid #3F3F46;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
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

        # Refresh
        act_refresh = menu.addAction("🔄 Refresh Balance Now")
        act_refresh.triggered.connect(self.trigger_refresh)

        menu.addSeparator()

        # Switch Size Mode
        if self.mode == "small":
            act_size = menu.addAction("📐 Switch to Medium Widget")
            act_size.triggered.connect(lambda: self.set_mode("medium"))
        else:
            act_size = menu.addAction("📐 Switch to Small Widget")
            act_size.triggered.connect(lambda: self.set_mode("small"))

        # Pin / Window Level
        act_ontop = menu.addAction("📌 Always on Top")
        act_ontop.setCheckable(True)
        act_ontop.setChecked(self.always_on_top)

        def toggle_ontop():
            self.always_on_top = not self.always_on_top
            if self.always_on_top:
                self.pinned_to_desktop = False
            SharedStorage.set_setting("widget_always_on_top", self.always_on_top)
            SharedStorage.set_setting("widget_pinned_to_desktop", self.pinned_to_desktop)
            self._update_window_flags()
            self.show()

        act_ontop.triggered.connect(toggle_ontop)

        menu.addSeparator()

        # Open Companion App
        act_companion = menu.addAction("🖥️ Open Companion App")
        act_companion.triggered.connect(self.open_companion_requested.emit)

        # Switch Active Key Submenu
        keys = SharedStorage.load_all_keys()
        if len(keys) > 1:
            key_menu = menu.addMenu("🔑 Switch Active Key")
            key_menu.setStyleSheet(menu.styleSheet())
            for k in keys:
                k_act = key_menu.addAction(f"{'✓ ' if k.is_widget_key else ''}{k.custom_label}")

                def select_key(key_id=k.id):
                    SharedStorage.set_widget_key(key_id)
                    self.load_data()
                    self.trigger_refresh()

                k_act.triggered.connect(select_key)

        menu.addSeparator()

        # Close Widget
        act_hide = menu.addAction("❌ Hide Desktop Widget")
        act_hide.triggered.connect(self.hide)

        menu.exec(event.globalPos())

    # MARK: - Custom Card Painting

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Outer bounding card
        margin = 6
        rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)

        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)

        # Dark sleek background
        painter.fillPath(path, QColor("#1C1C20"))

        # Subtle border
        border_pen = QPen(QColor(255, 255, 255, 22), 1)
        painter.setPen(border_pen)
        painter.drawPath(path)

        # Paint medium burn progress bar if present
        if self.mode == "medium" and hasattr(self, "burn_bar") and hasattr(self, "current_payload"):
            burn_rect = self.burn_bar.geometry()
            # Convert to self coordinates
            burn_global = self.burn_bar.mapTo(self, QPoint(0, 0))
            bx = burn_global.x()
            by = burn_global.y()
            bw = self.burn_bar.width()
            bh = self.burn_bar.height()

            if bw > 0:
                track_path = QPainterPath()
                track_path.addRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
                painter.fillPath(track_path, QColor(255, 255, 255, 25))

                burn_pct = self.current_payload.account_burn_percent
                if burn_pct > 0.0:
                    fill_w = max(bh, bw * burn_pct)
                    fill_path = QPainterPath()
                    fill_path.addRoundedRect(QRectF(bx, by, fill_w, bh), bh / 2.0, bh / 2.0)
                    painter.fillPath(fill_path, QColor(OpenRouterTheme.ELECTRIC_BLUE))
