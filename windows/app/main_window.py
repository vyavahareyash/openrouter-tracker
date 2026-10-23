"""Windows Companion Application matching macOS OpenRouterTrackerApp."""

from __future__ import annotations

import datetime
import threading
from typing import Dict, List, Optional

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
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from windows.app.add_key_dialog import AddKeyDialog
from windows.core.models import OpenRouterTheme, TrackedKey, WidgetPayload
from windows.core.service import OpenRouterService
from windows.core.storage import SharedStorage
from windows.widget.radial_gauge import RadialGauge


class KeyListItemWidget(QWidget):
    """Custom sidebar item widget with status dot, title, token, and percent pill."""

    def __init__(
        self,
        key: TrackedKey,
        payload: Optional[WidgetPayload],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.key = key
        self.payload = payload
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Dot
        dot_color = OpenRouterTheme.ELECTRIC_BLUE if self.key.is_widget_key else "#71717A"
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color: {dot_color}; font-size: 9px;")
        layout.addWidget(self.dot)

        # Text labels
        text_vbox = QVBoxLayout()
        text_vbox.setContentsMargins(0, 0, 0, 0)
        text_vbox.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(4)
        lbl_name = QLabel(self.key.custom_label)
        lbl_name.setStyleSheet("color: #F4F4F5; font-size: 13px; font-weight: 600;")
        name_row.addWidget(lbl_name)

        if self.key.is_widget_key:
            badge = QLabel("📌")
            badge.setStyleSheet("font-size: 10px;")
            name_row.addWidget(badge)

        name_row.addStretch()
        text_vbox.addLayout(name_row)

        lbl_token = QLabel(self.key.key_masked)
        lbl_token.setStyleSheet("color: #71717A; font-family: Consolas, monospace; font-size: 10px;")
        text_vbox.addWidget(lbl_token)

        layout.addLayout(text_vbox, stretch=1)

        # Percentage Pill
        if self.payload and self.payload.key_limit and self.payload.key_limit > 0:
            pct = self.payload.usage_percent
            pct_int = int(pct * 100)
            pill_color = OpenRouterTheme.get_gauge_color(pct)
            pill = QLabel(f"{pct_int}%")
            pill.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(255, 255, 255, 0.08);
                    color: {pill_color};
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 4px;
                    padding: 2px 6px;
                }}
            """)
            layout.addWidget(pill)


class StatCard(QWidget):
    """Reusable metric card with title, bold value, and subtitle."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str,
        val_color: str = "#F4F4F5",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #8C8C96; font-size: 11px; font-weight: 600;")
        layout.addWidget(lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"color: {val_color}; font-size: 17px; font-weight: bold;")
        layout.addWidget(self.lbl_value)

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("color: #55555C; font-size: 9px;")
        layout.addWidget(lbl_sub)

        self.setStyleSheet("""
            QWidget {
                background-color: #27272A;
                border-radius: 8px;
            }
        """)

    def set_value(self, value: str) -> None:
        self.lbl_value.setText(value)


class PeriodPill(QWidget):
    """Metric breakdown card for periodic spending."""

    def __init__(self, label: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        lbl_title = QLabel(label)
        lbl_title.setStyleSheet("color: #8C8C96; font-size: 10px;")
        layout.addWidget(lbl_title)

        self.lbl_val = QLabel("—")
        self.lbl_val.setStyleSheet("color: #F4F4F5; font-family: Consolas, monospace; font-size: 13px; font-weight: 600;")
        layout.addWidget(self.lbl_val)

        self.setStyleSheet("""
            QWidget {
                background-color: #27272A;
                border-radius: 8px;
            }
        """)

    def set_value(self, val: Optional[float]) -> None:
        if val is not None:
            self.lbl_val.setText(f"${val:.4f}")
        else:
            self.lbl_val.setText("—")


class MainWindow(QMainWindow):
    """OpenRouter Tracker Windows Companion App."""

    data_updated = Signal()
    _key_refreshed = Signal(str, object)  # Emits (key_id, payload)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("OpenRouter Tracker")
        self.setMinimumSize(860, 580)
        self.resize(920, 640)

        self.keys: List[TrackedKey] = []
        self.payloads: Dict[str, WidgetPayload] = {}
        self.selected_key_id: Optional[str] = None
        self._is_refreshing: bool = False
        self._is_editing_label: bool = False

        self._init_ui()
        self._key_refreshed.connect(self._on_key_refresh_completed)
        self.load_all_data()

    def _init_ui(self) -> None:
        # Dark modern theme styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #18181B;
                color: #F4F4F5;
            }
            QSplitter::handle {
                background-color: #27272A;
                width: 1px;
            }
            QListWidget {
                background-color: #18181B;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-radius: 8px;
                margin: 2px 8px;
            }
            QListWidget::item:selected {
                background-color: #3B82F6;
            }
            QListWidget::item:hover:!selected {
                background-color: #27272A;
            }
            QScrollArea {
                background-color: #18181B;
                border: none;
            }
            QPushButton {
                background-color: #27272A;
                color: #F4F4F5;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #3F3F46;
            }
        """)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(splitter)

        # 1. Left Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(270)
        sidebar.setStyleSheet("background-color: #18181B; border-right: 1px solid #27272A;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(12)

        lbl_section = QLabel("TRACKED KEYS")
        lbl_section.setStyleSheet("color: #71717A; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
        sidebar_layout.addWidget(lbl_section)

        self.list_keys = QListWidget()
        self.list_keys.currentRowChanged.connect(self._on_key_selected)
        sidebar_layout.addWidget(self.list_keys, stretch=1)

        btn_add = QPushButton("＋ Add API Key")
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.12);
                color: #3B82F6;
                border: 1px solid rgba(59, 130, 246, 0.25);
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.22);
            }
        """)
        btn_add.clicked.connect(self._open_add_key_dialog)
        sidebar_layout.addWidget(btn_add)

        splitter.addWidget(sidebar)

        # 2. Right Detail Panel
        self.detail_stack = QStackedWidget()
        self._build_empty_view()
        self._build_detail_view()
        splitter.addWidget(self.detail_stack)

    def _build_empty_view(self) -> None:
        empty_widget = QWidget()
        layout = QVBoxLayout(empty_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon_lbl = QLabel("🔑")
        icon_lbl.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("No API Keys Added")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        sub = QLabel("Add your OpenRouter key to track usage, balance, and desktop widgets.")
        sub.setStyleSheet("color: #71717A; font-size: 13px;")
        layout.addWidget(sub, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_first = QPushButton("Add Your First Key")
        btn_first.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        btn_first.clicked.connect(self._open_add_key_dialog)
        layout.addWidget(btn_first, alignment=Qt.AlignmentFlag.AlignCenter)

        self.detail_stack.addWidget(empty_widget)

    def _build_detail_view(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        detail_container = QWidget()
        self.detail_layout = QVBoxLayout(detail_container)
        self.detail_layout.setContentsMargins(28, 24, 28, 24)
        self.detail_layout.setSpacing(22)

        # Header Card
        self._build_header_card()

        # Primary Key Budget Section
        self._build_budget_section()

        # Secondary Account Overview Section
        self._build_account_section()

        self.detail_layout.addStretch()
        scroll.setWidget(detail_container)
        self.detail_stack.addWidget(scroll)

    def _build_header_card(self) -> None:
        header_hbox = QHBoxLayout()
        header_hbox.setSpacing(12)

        # Left title & edit
        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(4)

        edit_row = QHBoxLayout()
        edit_row.setSpacing(8)

        self.lbl_key_name = QLabel("API Key")
        self.lbl_key_name.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        edit_row.addWidget(self.lbl_key_name)

        self.txt_edit_name = QLineEdit()
        self.txt_edit_name.setStyleSheet("""
            QLineEdit {
                background-color: #27272A;
                color: #FFFFFF;
                border: 1px solid #3B82F6;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 15px;
            }
        """)
        self.txt_edit_name.hide()
        edit_row.addWidget(self.txt_edit_name)

        self.btn_edit_name = QPushButton("✏️")
        self.btn_edit_name.setFixedSize(26, 26)
        self.btn_edit_name.setToolTip("Rename Key")
        self.btn_edit_name.clicked.connect(self._toggle_edit_name)
        edit_row.addWidget(self.btn_edit_name)

        self.btn_save_name = QPushButton("Save")
        self.btn_save_name.setStyleSheet("background-color: #3B82F6; color: white;")
        self.btn_save_name.hide()
        self.btn_save_name.clicked.connect(self._save_edited_name)
        edit_row.addWidget(self.btn_save_name)

        edit_row.addStretch()
        left_vbox.addLayout(edit_row)

        sub_row = QHBoxLayout()
        sub_row.setSpacing(8)
        self.lbl_masked_token = QLabel("Token: ••••••••")
        self.lbl_masked_token.setStyleSheet("color: #71717A; font-family: Consolas, monospace; font-size: 12px;")
        sub_row.addWidget(self.lbl_masked_token)

        self.lbl_pinned_badge = QLabel("✓ Active on Desktop Widget")
        self.lbl_pinned_badge.setStyleSheet(f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 11px; font-weight: bold;")
        sub_row.addWidget(self.lbl_pinned_badge)

        sub_row.addStretch()
        left_vbox.addLayout(sub_row)
        header_hbox.addLayout(left_vbox, stretch=1)

        # Right Action Buttons
        actions_hbox = QHBoxLayout()
        actions_hbox.setSpacing(8)

        self.btn_pin = QPushButton("Pin to Widget")
        self.btn_pin.clicked.connect(self._toggle_pin_widget)
        actions_hbox.addWidget(self.btn_pin)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self._refresh_selected_key)
        actions_hbox.addWidget(self.btn_refresh)

        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setToolTip("Delete Key")
        self.btn_delete.setStyleSheet("QPushButton { color: #EF4444; border-color: rgba(239, 68, 68, 0.4); } QPushButton:hover { background-color: rgba(239, 68, 68, 0.15); }")
        self.btn_delete.clicked.connect(self._delete_selected_key)
        actions_hbox.addWidget(self.btn_delete)

        header_hbox.addLayout(actions_hbox)
        self.detail_layout.addLayout(header_hbox)

        # Error banner
        self.lbl_error_banner = QLabel()
        self.lbl_error_banner.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.12);
            color: #EF4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
        """)
        self.lbl_error_banner.hide()
        self.detail_layout.addWidget(self.lbl_error_banner)

    def _build_budget_section(self) -> None:
        sec_header = QHBoxLayout()
        lbl_title = QLabel("Key Budget & Usage")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F4F4F5;")
        sec_header.addWidget(lbl_title)
        sec_header.addStretch()

        self.lbl_last_updated = QLabel("Updated just now")
        self.lbl_last_updated.setStyleSheet("color: #71717A; font-size: 11px;")
        sec_header.addWidget(self.lbl_last_updated)
        self.detail_layout.addLayout(sec_header)

        # Visual Gauge + Numbers Card
        budget_card = QWidget()
        budget_card.setStyleSheet("background-color: #202024; border-radius: 12px;")
        card_layout = QHBoxLayout(budget_card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(24)

        # Gauge
        self.detail_gauge = RadialGauge(stroke_width=11.0)
        self.detail_gauge.setFixedSize(116, 116)
        card_layout.addWidget(self.detail_gauge)

        # Stats Grid
        stats_vbox = QVBoxLayout()
        stats_vbox.setSpacing(10)
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self.card_spend = StatCard("Key Spend", "$0.0000", "USD", OpenRouterTheme.NEON_VIOLET)
        self.card_rem = StatCard("Remaining Budget", "$0.0000", "USD", OpenRouterTheme.EMERALD_GREEN)
        self.card_limit = StatCard("Assigned Limit", "Unlimited", "USD", OpenRouterTheme.AMBER_WARNING)

        stats_row.addWidget(self.card_spend)
        stats_row.addWidget(self.card_rem)
        stats_row.addWidget(self.card_limit)
        stats_vbox.addLayout(stats_row)

        card_layout.addLayout(stats_vbox, stretch=1)
        self.detail_layout.addWidget(budget_card)

        # Periodic Spend Breakdown Pills
        period_row = QHBoxLayout()
        period_row.setSpacing(12)
        self.pill_today = PeriodPill("Today's Spend")
        self.pill_week = PeriodPill("This Week")
        self.pill_month = PeriodPill("This Month")

        period_row.addWidget(self.pill_today)
        period_row.addWidget(self.pill_week)
        period_row.addWidget(self.pill_month)
        self.detail_layout.addLayout(period_row)

    def _build_account_section(self) -> None:
        lbl_sec2 = QLabel("Account Overview (Shared Balance)")
        lbl_sec2.setStyleSheet("font-size: 15px; font-weight: bold; color: #A1A1AA; margin-top: 8px;")
        self.detail_layout.addWidget(lbl_sec2)

        acct_card = QWidget()
        acct_card.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(59, 130, 246, 0.05);
                border: 1px solid rgba(59, 130, 246, 0.18);
                border-radius: 12px;
            }}
        """)
        acct_layout = QVBoxLayout(acct_card)
        acct_layout.setContentsMargins(18, 16, 18, 16)
        acct_layout.setSpacing(14)

        top_row = QHBoxLayout()
        bal_vbox = QVBoxLayout()
        bal_vbox.setSpacing(2)
        lbl_bal_caption = QLabel("Available Account Balance")
        lbl_bal_caption.setStyleSheet("color: #8C8C96; font-size: 12px; border: none; background: transparent;")
        self.lbl_acct_bal = QLabel("$0.00")
        self.lbl_acct_bal.setStyleSheet(f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 26px; font-weight: bold; border: none; background: transparent;")
        bal_vbox.addWidget(lbl_bal_caption)
        bal_vbox.addWidget(self.lbl_acct_bal)
        top_row.addLayout(bal_vbox)

        top_row.addStretch()

        totals_hbox = QHBoxLayout()
        totals_hbox.setSpacing(20)
        tot_vbox = QVBoxLayout()
        tot_vbox.setSpacing(2)
        lbl_tot_cap = QLabel("Total Purchased")
        lbl_tot_cap.setStyleSheet("color: #8C8C96; font-size: 11px; border: none; background: transparent;")
        self.lbl_acct_total = QLabel("$0.00")
        self.lbl_acct_total.setStyleSheet("color: #F4F4F5; font-size: 15px; font-family: Consolas, monospace; font-weight: 600; border: none; background: transparent;")
        tot_vbox.addWidget(lbl_tot_cap)
        tot_vbox.addWidget(self.lbl_acct_total)
        totals_hbox.addLayout(tot_vbox)

        burn_vbox = QVBoxLayout()
        burn_vbox.setSpacing(2)
        lbl_burn_cap = QLabel("Account Burn")
        lbl_burn_cap.setStyleSheet("color: #8C8C96; font-size: 11px; border: none; background: transparent;")
        self.lbl_acct_burn = QLabel("$0.00")
        self.lbl_acct_burn.setStyleSheet("color: #F4F4F5; font-size: 15px; font-family: Consolas, monospace; font-weight: 600; border: none; background: transparent;")
        burn_vbox.addWidget(lbl_burn_cap)
        burn_vbox.addWidget(self.lbl_acct_burn)
        totals_hbox.addLayout(burn_vbox)

        top_row.addLayout(totals_hbox)
        acct_layout.addLayout(top_row)

        # Progress bar
        self.account_bar = QWidget()
        self.account_bar.setFixedHeight(6)
        self.account_bar.setStyleSheet("background: transparent; border: none;")
        acct_layout.addWidget(self.account_bar)

        sub_stats = QHBoxLayout()
        self.lbl_bar_stat1 = QLabel("Total used: $0.00 (0%)")
        self.lbl_bar_stat1.setStyleSheet("color: #71717A; font-size: 11px; border: none; background: transparent;")
        self.lbl_bar_stat2 = QLabel("Credits pool: $0.00")
        self.lbl_bar_stat2.setStyleSheet("color: #71717A; font-size: 11px; border: none; background: transparent;")
        sub_stats.addWidget(self.lbl_bar_stat1)
        sub_stats.addStretch()
        sub_stats.addWidget(self.lbl_bar_stat2)
        acct_layout.addLayout(sub_stats)

        self.detail_layout.addWidget(acct_card)

    # MARK: - Data Loading & Key Selection

    def load_all_data(self) -> None:
        self.keys = SharedStorage.load_all_keys()
        self.list_keys.clear()

        for k in self.keys:
            payload = SharedStorage.get_payload(k.id)
            if payload:
                self.payloads[k.id] = payload

            item = QListWidgetItem(self.list_keys)
            item.setSizeHint(QSize(250, 56))
            widget = KeyListItemWidget(k, payload)
            self.list_keys.setItemWidget(item, widget)

        if not self.keys:
            self.detail_stack.setCurrentIndex(0)
            self.selected_key_id = None
        else:
            self.detail_stack.setCurrentIndex(1)
            # Find widget key or select first
            widget_idx = next((i for i, k in enumerate(self.keys) if k.is_widget_key), 0)
            self.list_keys.setCurrentRow(widget_idx)

    def _on_key_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.keys):
            return
        key = self.keys[row]
        self.selected_key_id = key.id
        self._display_key(key)

    def _display_key(self, key: TrackedKey) -> None:
        self.lbl_key_name.setText(key.custom_label)
        self.txt_edit_name.setText(key.custom_label)
        self.lbl_masked_token.setText(f"Token: {key.key_masked}")

        if key.is_widget_key:
            self.lbl_pinned_badge.show()
            self.btn_pin.setText("Pinned to Widget")
            self.btn_pin.setStyleSheet(f"background-color: {OpenRouterTheme.ELECTRIC_BLUE}; color: white;")
        else:
            self.lbl_pinned_badge.hide()
            self.btn_pin.setText("Pin to Widget")
            self.btn_pin.setStyleSheet("")

        payload = self.payloads.get(key.id) or SharedStorage.get_payload(key.id)
        if not payload:
            payload = WidgetPayload.empty()
            payload.custom_nickname = key.custom_label
            payload.key_masked = key.key_masked

        self._render_payload(payload)

    def _render_payload(self, payload: WidgetPayload) -> None:
        self.current_payload = payload

        if payload.error_message:
            self.lbl_error_banner.setText(f"⚠️ {payload.error_message}")
            self.lbl_error_banner.show()
        else:
            self.lbl_error_banner.hide()

        try:
            dt = datetime.datetime.fromisoformat(payload.last_updated)
            self.lbl_last_updated.setText(f"Updated {dt.strftime('%H:%M:%S')}")
        except Exception:
            self.lbl_last_updated.setText("Updated recently")

        self.detail_gauge.set_payload(payload)
        self.card_spend.set_value(f"${payload.key_usage:.4f}")

        if payload.key_remaining is not None:
            self.card_rem.set_value(f"${payload.key_remaining:.4f}")
        else:
            self.card_rem.set_value("—")

        if payload.key_limit is not None and payload.key_limit > 0:
            self.card_limit.set_value(f"${payload.key_limit:.2f}")
        else:
            self.card_limit.set_value("Unlimited")

        self.pill_today.set_value(payload.usage_daily)
        self.pill_week.set_value(payload.usage_weekly)
        self.pill_month.set_value(payload.usage_monthly)

        self.lbl_acct_bal.setText(f"${payload.total_balance:.2f}")
        self.lbl_acct_total.setText(f"${payload.total_credits:.2f}")
        self.lbl_acct_burn.setText(f"${payload.total_usage:.2f}")

        burn_pct_int = int(payload.account_burn_percent * 100)
        self.lbl_bar_stat1.setText(f"Total used: ${payload.total_usage:.2f} ({burn_pct_int}%)")
        self.lbl_bar_stat2.setText(f"Credits pool: ${payload.total_credits:.2f}")

        self.update()

    # MARK: - Actions

    def _open_add_key_dialog(self) -> None:
        dlg = AddKeyDialog(self)
        dlg.key_validated_and_added.connect(self._on_key_added)
        dlg.exec()

    def _on_key_added(self, new_key: TrackedKey) -> None:
        self.load_all_data()
        self.data_updated.emit()

    def _toggle_edit_name(self) -> None:
        self._is_editing_label = not self._is_editing_label
        if self._is_editing_label:
            self.lbl_key_name.hide()
            self.txt_edit_name.show()
            self.btn_save_name.show()
            self.txt_edit_name.setFocus()
        else:
            self.lbl_key_name.show()
            self.txt_edit_name.hide()
            self.btn_save_name.hide()

    def _save_edited_name(self) -> None:
        if not self.selected_key_id:
            return
        new_name = self.txt_edit_name.text().strip()
        if not new_name:
            return

        key = next((k for k in self.keys if k.id == self.selected_key_id), None)
        if key:
            key.custom_label = new_name
            SharedStorage.update_key(key)
            self._toggle_edit_name()
            self.load_all_data()
            self.data_updated.emit()

    def _toggle_pin_widget(self) -> None:
        if not self.selected_key_id:
            return
        SharedStorage.set_widget_key(self.selected_key_id)
        self.load_all_data()
        self.data_updated.emit()

    def _delete_selected_key(self) -> None:
        if not self.selected_key_id:
            return
        key = next((k for k in self.keys if k.id == self.selected_key_id), None)
        if not key:
            return

        confirm = QMessageBox.question(
            self,
            "Delete API Key",
            f"Are you sure you want to permanently delete '{key.custom_label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            SharedStorage.delete_key(key.id)
            self.load_all_data()
            self.data_updated.emit()

    def _refresh_selected_key(self) -> None:
        if not self.selected_key_id or self._is_refreshing:
            return
        key = next((k for k in self.keys if k.id == self.selected_key_id), None)
        if not key:
            return

        self._is_refreshing = True
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.setText("⏳ Refreshing...")

        def worker():
            try:
                payload = OpenRouterService.refresh_key(key)
            except Exception as e:
                payload = WidgetPayload.empty()
                payload.error_message = str(e)
            self._key_refreshed.emit(key.id, payload)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_key_refresh_completed(self, key_id: str, payload: WidgetPayload) -> None:
        self._is_refreshing = False
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("🔄 Refresh")
        self.payloads[key_id] = payload
        if self.selected_key_id == key_id:
            self._render_payload(payload)
        self.data_updated.emit()
