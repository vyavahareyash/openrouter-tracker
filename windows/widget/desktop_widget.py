"""Windows Desktop Widget with Small & Medium layouts, frameless drag, 1-click refresh, and Light/Dark themes."""

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
from windows.core.theme import ThemeManager
from windows.widget.radial_gauge import RadialGauge


class RefreshButton(QPushButton):
    """Tactile 1-click refresh button with subtle hover and spinning/loading state."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("🔄", parent)
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Refresh OpenRouter balance now")
        self.theme = ThemeManager.get_instance()
        self.apply_theme()

    def apply_theme(self) -> None:
        if self.theme.is_dark():
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
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 0.06);
                    color: #64748B;
                    border: none;
                    border-radius: 11px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(59, 130, 246, 0.20);
                    color: #1E40AF;
                }
                QPushButton:pressed {
                    background-color: rgba(59, 130, 246, 0.40);
                }
                QPushButton:disabled {
                    color: #CBD5E1;
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
        self.theme = ThemeManager.get_instance()
        self.theme.theme_changed.connect(self._on_theme_changed)

        self._init_window()
        self._init_ui()
        self.load_data()
        self.refresh_completed.connect(self._on_refresh_done)

    def _init_window(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._update_window_flags()

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
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(10, 10, 10, 10)
        self.root_layout.setSpacing(0)

        self.card = QWidget(self)
        self.card.setObjectName("widgetCard")
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(10, 10, 10, 10)
        self.card_layout.setSpacing(6)
        self.root_layout.addWidget(self.card)

        self._build_content()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)

    def _build_content(self) -> None:
        self._clear_layout(self.card_layout)

        if self.mode == "medium":
            self._build_medium_layout()
        else:
            self._build_small_layout()

        self.apply_theme()

    def _build_small_layout(self) -> None:
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {OpenRouterTheme.NEON_VIOLET}; font-size: 8px; background: transparent; border: none;")
        header.addWidget(dot)

        self.lbl_nickname = QLabel("OpenRouter")
        self.lbl_nickname.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header.addWidget(self.lbl_nickname)

        self.btn_refresh = RefreshButton()
        self.btn_refresh.clicked.connect(self.trigger_refresh)
        header.addWidget(self.btn_refresh)
        self.card_layout.addLayout(header)

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

        key_header = QHBoxLayout()
        key_header.setSpacing(4)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 8px; background: transparent; border: none;")
        key_header.addWidget(dot)

        self.lbl_nickname = QLabel("OpenRouter")
        key_header.addWidget(self.lbl_nickname)
        key_header.addStretch()
        left_vbox.addLayout(key_header)

        self.lbl_masked = QLabel("••••••••")
        left_vbox.addWidget(self.lbl_masked)

        left_vbox.addSpacing(2)

        gauge_row = QHBoxLayout()
        gauge_row.setContentsMargins(0, 0, 0, 0)
        gauge_row.setSpacing(8)

        self.radial_gauge = RadialGauge(stroke_width=6.0)
        self.radial_gauge.setFixedSize(82, 82)
        gauge_row.addWidget(self.radial_gauge)

        stats_vbox = QVBoxLayout()
        stats_vbox.setContentsMargins(0, 0, 0, 0)
        stats_vbox.setSpacing(4)

        self.lbl_spent_title = QLabel("SPENT")
        self.lbl_spent_val = QLabel("$0.00")
        self.lbl_limit_title = QLabel("LIMIT")
        self.lbl_limit_val = QLabel("Unlimited")

        stats_vbox.addWidget(self.lbl_spent_title)
        stats_vbox.addWidget(self.lbl_spent_val)
        stats_vbox.addSpacing(2)
        stats_vbox.addWidget(self.lbl_limit_title)
        stats_vbox.addWidget(self.lbl_limit_val)
        stats_vbox.addStretch()

        gauge_row.addLayout(stats_vbox)
        left_vbox.addLayout(gauge_row)
        left_vbox.addStretch()
        main_hbox.addLayout(left_vbox, stretch=3)

        # Divider
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.VLine)
        main_hbox.addWidget(self.divider)

        # Right Column: Account Overview Card
        self.right_card = QFrame()
        self.right_card.setObjectName("rightAccountCard")
        right_vbox = QVBoxLayout(self.right_card)
        right_vbox.setContentsMargins(8, 6, 8, 6)
        right_vbox.setSpacing(3)

        acct_header = QHBoxLayout()
        self.lbl_acct_title = QLabel("Account Total")
        acct_header.addWidget(self.lbl_acct_title)
        acct_header.addStretch()

        self.btn_refresh = RefreshButton()
        self.btn_refresh.clicked.connect(self.trigger_refresh)
        acct_header.addWidget(self.btn_refresh)
        right_vbox.addLayout(acct_header)

        self.lbl_bal_caption = QLabel("Available Balance")
        right_vbox.addWidget(self.lbl_bal_caption)

        self.lbl_acct_balance = QLabel("$0.00")
        right_vbox.addWidget(self.lbl_acct_balance)

        self.burn_bar = QWidget()
        self.burn_bar.setFixedHeight(4)
        self.burn_bar.setStyleSheet("background: transparent; border: none;")
        right_vbox.addWidget(self.burn_bar)

        burn_stats = QHBoxLayout()
        burn_stats.setContentsMargins(0, 0, 0, 0)
        self.lbl_burn_used = QLabel("Used $0")
        self.lbl_burn_total = QLabel("Total $0")
        burn_stats.addWidget(self.lbl_burn_used)
        burn_stats.addStretch()
        burn_stats.addWidget(self.lbl_burn_total)
        right_vbox.addLayout(burn_stats)

        right_vbox.addStretch()

        self.lbl_updated = QLabel("Updated just now")
        self.lbl_updated.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_vbox.addWidget(self.lbl_updated)

        main_hbox.addWidget(self.right_card, stretch=2)
        self.card_layout.addLayout(main_hbox)

    def apply_theme(self) -> None:
        is_dark = self.theme.is_dark()
        pri = self.theme.text_primary
        sec = self.theme.text_secondary
        muted = self.theme.text_muted

        if hasattr(self, "lbl_nickname"):
            self.lbl_nickname.setStyleSheet(f"color: {pri}; font-size: 11px; font-weight: bold; background: transparent; border: none;")

        if hasattr(self, "btn_refresh"):
            self.btn_refresh.apply_theme()

        if hasattr(self, "radial_gauge"):
            self.radial_gauge.update()

        if self.mode == "medium":
            if hasattr(self, "lbl_masked"):
                self.lbl_masked.setStyleSheet(f"color: {muted}; font-family: Consolas, monospace; font-size: 8px; background: transparent; border: none;")
            if hasattr(self, "lbl_spent_title"):
                self.lbl_spent_title.setStyleSheet(f"color: {sec}; font-size: 7px; font-weight: bold; background: transparent; border: none;")
            if hasattr(self, "lbl_spent_val"):
                self.lbl_spent_val.setStyleSheet(f"color: {OpenRouterTheme.NEON_VIOLET}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            if hasattr(self, "lbl_limit_title"):
                self.lbl_limit_title.setStyleSheet(f"color: {sec}; font-size: 7px; font-weight: bold; background: transparent; border: none;")
            if hasattr(self, "lbl_limit_val"):
                self.lbl_limit_val.setStyleSheet(f"color: {OpenRouterTheme.AMBER_WARNING}; font-size: 11px; font-weight: bold; background: transparent; border: none;")
            if hasattr(self, "divider"):
                div_color = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.08)"
                self.divider.setStyleSheet(f"color: {div_color};")
            if hasattr(self, "right_card"):
                border_col = "rgba(59, 130, 246, 0.18)" if is_dark else "rgba(59, 130, 246, 0.22)"
                self.right_card.setStyleSheet(f"""
                    QFrame#rightAccountCard {{
                        background-color: rgba(59, 130, 246, 0.08);
                        border: 1px solid {border_col};
                        border-radius: 8px;
                    }}
                """)
            if hasattr(self, "lbl_acct_title"):
                self.lbl_acct_title.setStyleSheet(f"color: {sec}; font-size: 9px; font-weight: 600; border: none; background: transparent;")
            if hasattr(self, "lbl_bal_caption"):
                self.lbl_bal_caption.setStyleSheet(f"color: {sec}; font-size: 8px; border: none; background: transparent;")
            if hasattr(self, "lbl_acct_balance"):
                self.lbl_acct_balance.setStyleSheet(f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 15px; font-weight: bold; border: none; background: transparent;")
            if hasattr(self, "lbl_burn_used"):
                self.lbl_burn_used.setStyleSheet(f"color: {sec}; font-size: 7.5px; border: none; background: transparent;")
            if hasattr(self, "lbl_burn_total"):
                self.lbl_burn_total.setStyleSheet(f"color: {sec}; font-size: 7.5px; border: none; background: transparent;")
            if hasattr(self, "lbl_updated"):
                self.lbl_updated.setStyleSheet(f"color: {muted}; font-size: 7px; border: none; background: transparent;")

        self.update()

    def _on_theme_changed(self) -> None:
        self.apply_theme()
        self.load_data()

    def load_data(self) -> None:
        self.theme.sync_from_storage()
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

    def set_mode(self, mode: str) -> None:
        if mode not in ("small", "medium"):
            return
        self.mode = mode
        SharedStorage.set_setting("widget_mode", mode)
        target_size = self.MEDIUM_SIZE if mode == "medium" else self.SMALL_SIZE
        self.setFixedSize(target_size)
        self._build_content()
        self.load_data()

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

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu_bg = "#27272A" if self.theme.is_dark() else "#FFFFFF"
        menu_text = "#F4F4F5" if self.theme.is_dark() else "#0F172A"
        menu_border = "#3F3F46" if self.theme.is_dark() else "#E2E8F0"
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_text};
                border: 1px solid {menu_border};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: #3B82F6;
                color: #FFFFFF;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {menu_border};
                margin: 4px 6px;
            }}
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

        # Theme Submenu
        theme_menu = menu.addMenu("🎨 Theme")
        theme_menu.setStyleSheet(menu.styleSheet())
        act_sys = theme_menu.addAction("💻 System Default")
        act_sys.setCheckable(True)
        act_sys.setChecked(self.theme.mode == "system")
        act_sys.triggered.connect(lambda: self.theme.set_mode("system"))

        act_dark = theme_menu.addAction("🌙 Dark Mode")
        act_dark.setCheckable(True)
        act_dark.setChecked(self.theme.mode == "dark")
        act_dark.triggered.connect(lambda: self.theme.set_mode("dark"))

        act_light = theme_menu.addAction("☀️ Light Mode")
        act_light.setCheckable(True)
        act_light.setChecked(self.theme.mode == "light")
        act_light.triggered.connect(lambda: self.theme.set_mode("light"))

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

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        margin = 6
        rect = QRectF(margin, margin, self.width() - 2 * margin, self.height() - 2 * margin)

        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)

        # Dynamic card background
        painter.fillPath(path, self.theme.widget_bg_qcolor)

        # Subtle border
        border_pen = QPen(self.theme.widget_border_qcolor, 1)
        painter.setPen(border_pen)
        painter.drawPath(path)

        # Paint medium burn progress bar
        if self.mode == "medium" and hasattr(self, "burn_bar") and hasattr(self, "current_payload"):
            burn_global = self.burn_bar.mapTo(self, QPoint(0, 0))
            bx = burn_global.x()
            by = burn_global.y()
            bw = self.burn_bar.width()
            bh = self.burn_bar.height()

            if bw > 0:
                track_path = QPainterPath()
                track_path.addRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
                painter.fillPath(track_path, self.theme.burn_track_qcolor)

                burn_pct = self.current_payload.account_burn_percent
                if burn_pct > 0.0:
                    fill_w = max(bh, bw * burn_pct)
                    fill_path = QPainterPath()
                    fill_path.addRoundedRect(QRectF(bx, by, fill_w, bh), bh / 2.0, bh / 2.0)
                    painter.fillPath(fill_path, QColor(OpenRouterTheme.ELECTRIC_BLUE))
