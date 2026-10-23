"""Windows Companion Application matching macOS OpenRouterTrackerApp with Light & Dark themes."""

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
    QMenu,
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
from windows.core.theme import ThemeManager
from windows.widget.radial_gauge import RadialGauge


class KeyListItemWidget(QFrame):
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
        self.theme = ThemeManager.get_instance()
        self.is_selected: bool = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Dot
        self.dot = QLabel("●")
        layout.addWidget(self.dot)

        # Text labels
        text_vbox = QVBoxLayout()
        text_vbox.setContentsMargins(0, 0, 0, 0)
        text_vbox.setSpacing(2)

        name_row = QHBoxLayout()
        name_row.setSpacing(4)
        self.lbl_name = QLabel(self.key.custom_label)
        name_row.addWidget(self.lbl_name)

        if self.key.is_widget_key:
            self.badge = QLabel("📌")
            name_row.addWidget(self.badge)

        name_row.addStretch()
        text_vbox.addLayout(name_row)

        self.lbl_token = QLabel(self.key.key_masked)
        text_vbox.addWidget(self.lbl_token)

        layout.addLayout(text_vbox, stretch=1)

        # Percentage Pill
        if self.payload and self.payload.key_limit and self.payload.key_limit > 0:
            pct = self.payload.usage_percent
            pct_int = int(pct * 100)
            self.pill = QLabel(f"{pct_int}%")
            layout.addWidget(self.pill)

        self.apply_theme()

    def set_selected(self, selected: bool) -> None:
        self.is_selected = selected
        self.apply_theme()

    def apply_theme(self) -> None:
        is_dark = self.theme.is_dark()
        if self.is_selected:
            self.setStyleSheet("""
                KeyListItemWidget {
                    background-color: #3B82F6;
                    border-radius: 8px;
                    border: none;
                }
            """)
            dot_color = "#FFFFFF" if self.key.is_widget_key else "rgba(255, 255, 255, 0.55)"
            self.dot.setStyleSheet(f"color: {dot_color}; font-size: 9px; background: transparent; border: none;")
            self.lbl_name.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            if hasattr(self, "badge"):
                self.badge.setStyleSheet("font-size: 10px; background: transparent; border: none;")
            self.lbl_token.setStyleSheet("color: rgba(255, 255, 255, 0.85); font-family: Consolas, monospace; font-size: 10px; background: transparent; border: none;")
            if hasattr(self, "pill"):
                self.pill.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 255, 255, 0.22);
                        color: #FFFFFF;
                        font-size: 11px;
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 2px 6px;
                        border: none;
                    }
                """)
        else:
            hover_bg = "rgba(255, 255, 255, 0.06)" if is_dark else "rgba(0, 0, 0, 0.05)"
            self.setStyleSheet(f"""
                KeyListItemWidget {{
                    background-color: transparent;
                    border-radius: 8px;
                    border: none;
                }}
                KeyListItemWidget:hover {{
                    background-color: {hover_bg};
                }}
            """)
            dot_color = OpenRouterTheme.ELECTRIC_BLUE if self.key.is_widget_key else self.theme.text_muted
            self.dot.setStyleSheet(f"color: {dot_color}; font-size: 9px; background: transparent; border: none;")
            self.lbl_name.setStyleSheet(f"color: {self.theme.text_primary}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            if hasattr(self, "badge"):
                self.badge.setStyleSheet("font-size: 10px; background: transparent; border: none;")
            self.lbl_token.setStyleSheet(f"color: {self.theme.text_secondary}; font-family: Consolas, monospace; font-size: 10px; background: transparent; border: none;")
            if hasattr(self, "pill") and self.payload and self.payload.key_limit and self.payload.key_limit > 0:
                pct = self.payload.usage_percent
                pill_color = OpenRouterTheme.get_gauge_color(pct)
                bg_col = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(0, 0, 0, 0.05)"
                self.pill.setStyleSheet(f"""
                    QLabel {{
                        background-color: {bg_col};
                        color: {pill_color};
                        font-size: 11px;
                        font-weight: bold;
                        border-radius: 4px;
                        padding: 2px 6px;
                        border: none;
                    }}
                """)

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        p = self.parent()
        while p and not isinstance(p, QListWidget):
            p = p.parent()
        if isinstance(p, QListWidget):
            for i in range(p.count()):
                if p.itemWidget(p.item(i)) is self:
                    p.setCurrentRow(i)
                    break


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
        self.setObjectName("statCard")
        self.theme = ThemeManager.get_instance()
        self.val_color = val_color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        layout.addWidget(self.lbl_title)

        self.lbl_value = QLabel(value)
        layout.addWidget(self.lbl_value)

        self.lbl_sub = QLabel(subtitle)
        layout.addWidget(self.lbl_sub)

        self.apply_theme()

    def apply_theme(self) -> None:
        self.lbl_title.setStyleSheet(f"color: {self.theme.text_secondary}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        self.lbl_value.setStyleSheet(f"color: {self.val_color}; font-size: 17px; font-weight: bold; background: transparent; border: none;")
        self.lbl_sub.setStyleSheet(f"color: {self.theme.text_muted}; font-size: 9px; background: transparent; border: none;")
        self.setStyleSheet(f"""
            StatCard#statCard {{
                background-color: {self.theme.card_bg};
                border: 1px solid {self.theme.card_border};
                border-radius: 8px;
            }}
            StatCard QLabel {{
                background: transparent;
                border: none;
            }}
        """)

    def set_value(self, value: str) -> None:
        self.lbl_value.setText(value)


class PeriodPill(QWidget):
    """Metric breakdown card for periodic spending."""

    def __init__(self, label: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("periodPill")
        self.theme = ThemeManager.get_instance()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        self.lbl_title = QLabel(label)
        layout.addWidget(self.lbl_title)

        self.lbl_val = QLabel("—")
        layout.addWidget(self.lbl_val)

        self.apply_theme()

    def apply_theme(self) -> None:
        self.lbl_title.setStyleSheet(f"color: {self.theme.text_secondary}; font-size: 10px; background: transparent; border: none;")
        self.lbl_val.setStyleSheet(f"color: {self.theme.text_primary}; font-family: Consolas, monospace; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        self.setStyleSheet(f"""
            PeriodPill#periodPill {{
                background-color: {self.theme.card_bg};
                border: 1px solid {self.theme.card_border};
                border-radius: 8px;
            }}
            PeriodPill QLabel {{
                background: transparent;
                border: none;
            }}
        """)

    def set_value(self, val: Optional[float]) -> None:
        if val is not None:
            self.lbl_val.setText(f"${val:.4f}")
        else:
            self.lbl_val.setText("—")


class AccountBurnBar(QWidget):
    """Clean capsule progress bar displaying account burn percentage."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("accountBurnBar")
        self.setFixedHeight(6)
        self.burn_pct: float = 0.0
        self.theme = ThemeManager.get_instance()
        self.theme.theme_changed.connect(self.update)

    def set_percent(self, pct: float) -> None:
        self.burn_pct = max(0.0, min(1.0, pct))
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = float(self.width())
        h = float(self.height())
        r = h / 2.0

        # Background track
        track_path = QPainterPath()
        track_path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        painter.fillPath(track_path, self.theme.burn_track_qcolor)

        # Progress fill
        if self.burn_pct > 0.0:
            fill_w = max(h, w * self.burn_pct)
            fill_path = QPainterPath()
            fill_path.addRoundedRect(QRectF(0, 0, fill_w, h), r, r)
            painter.fillPath(fill_path, QColor(OpenRouterTheme.ELECTRIC_BLUE))


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

        self.theme = ThemeManager.get_instance()
        self.theme.theme_changed.connect(self._on_theme_changed)

        self._init_ui()
        self._key_refreshed.connect(self._on_key_refresh_completed)
        self.load_all_data()

    def _init_ui(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setObjectName("mainSplitter")
        self.setCentralWidget(self.splitter)

        # 1. Left Sidebar
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(270)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(12)

        self.lbl_section = QLabel("TRACKED KEYS")
        self.lbl_section.setObjectName("lblSection")
        sidebar_layout.addWidget(self.lbl_section)

        self.list_keys = QListWidget()
        self.list_keys.setObjectName("list_keys")
        self.list_keys.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_keys.currentRowChanged.connect(self._on_key_selected)
        sidebar_layout.addWidget(self.list_keys, stretch=1)

        self.btn_add = QPushButton("＋ Add API Key")
        self.btn_add.setObjectName("btnAdd")
        self.btn_add.clicked.connect(self._open_add_key_dialog)
        sidebar_layout.addWidget(self.btn_add)

        self.splitter.addWidget(self.sidebar)

        # 2. Right Detail Panel
        self.detail_stack = QStackedWidget()
        self.detail_stack.setObjectName("detailStack")
        self._build_empty_view()
        self._build_detail_view()
        self.splitter.addWidget(self.detail_stack)

        self._apply_theme_styles()

    def _apply_theme_styles(self) -> None:
        is_dark = self.theme.is_dark()
        bg = self.theme.bg_color
        card_bg = self.theme.card_bg
        card_border = self.theme.card_border
        text = self.theme.text_primary
        muted = self.theme.text_muted
        sec = self.theme.text_secondary
        sb_bg = self.theme.sidebar_bg
        sb_border = self.theme.sidebar_border

        btn_bg = "#27272A" if is_dark else "#FFFFFF"
        btn_hover = "#3F3F46" if is_dark else "#F1F5F9"
        btn_border = "#3F3F46" if is_dark else "#CBD5E1"

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg};
                color: {text};
            }}
            QSplitter::handle {{
                background-color: {sb_border};
                width: 1px;
            }}
            QWidget#sidebar {{
                background-color: {sb_bg};
                border-right: 1px solid {sb_border};
            }}
            QListWidget#list_keys {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget#list_keys::item {{
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 2px 4px;
                border-radius: 8px;
            }}
            QListWidget#list_keys::item:selected {{
                background-color: transparent;
                border: none;
            }}
            QListWidget#list_keys::item:hover:!selected {{
                background-color: transparent;
                border: none;
            }}
            QStackedWidget#detailStack {{
                background-color: {bg};
            }}
            QWidget#emptyWidget {{
                background-color: {bg};
            }}
            QScrollArea#detailScrollArea {{
                background-color: {bg};
                border: none;
            }}
            QWidget#detailContainer {{
                background-color: {bg};
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text};
                border: 1px solid {btn_border};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {'rgba(255, 255, 255, 0.18)' if is_dark else 'rgba(0, 0, 0, 0.18)'};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {'rgba(255, 255, 255, 0.32)' if is_dark else 'rgba(0, 0, 0, 0.32)'};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                height: 0px;
            }}
        """)

        # Explicitly ensure viewport and container have the dark/light background
        if hasattr(self, "scroll") and self.scroll.viewport():
            self.scroll.viewport().setStyleSheet(f"background-color: {bg};")
            self.scroll.viewport().setAutoFillBackground(False)
        if hasattr(self, "detail_container"):
            self.detail_container.setStyleSheet(f"background-color: {bg};")
            self.detail_container.setAutoFillBackground(False)

        # 1. Sidebar section label
        self.lbl_section.setStyleSheet(
            f"color: {muted}; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; background: transparent; border: none;"
        )

        # 2. Sidebar key list items
        for i in range(self.list_keys.count()):
            item = self.list_keys.item(i)
            w = self.list_keys.itemWidget(item)
            if isinstance(w, KeyListItemWidget):
                w.apply_theme()

        # 3. Add Key button
        self.btn_add.setStyleSheet("""
            QPushButton#btnAdd {
                background-color: rgba(59, 130, 246, 0.12);
                color: #3B82F6;
                border: 1px solid rgba(59, 130, 246, 0.25);
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#btnAdd:hover {
                background-color: rgba(59, 130, 246, 0.22);
            }
        """)

        # 4. Empty View
        if hasattr(self, "lbl_empty_title"):
            self.lbl_empty_title.setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {text}; background: transparent; border: none;"
            )
            self.lbl_empty_sub.setStyleSheet(
                f"color: {muted}; font-size: 13px; background: transparent; border: none;"
            )

        # 5. Header card elements (Key Name, Token, Buttons)
        if hasattr(self, "lbl_key_name"):
            self.lbl_key_name.setStyleSheet(
                f"font-size: 22px; font-weight: bold; color: {text}; background: transparent; border: none;"
            )

        if hasattr(self, "txt_edit_name"):
            self.txt_edit_name.setStyleSheet(f"""
                QLineEdit#txtEditName {{
                    background-color: {card_bg};
                    color: {text};
                    border: 1px solid #3B82F6;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 15px;
                }}
            """)

        if hasattr(self, "btn_edit_name"):
            self.btn_edit_name.setStyleSheet(f"""
                QPushButton#btnEditName {{
                    background-color: {btn_bg};
                    color: {text};
                    border: 1px solid {btn_border};
                    border-radius: 6px;
                    padding: 0px;
                    font-size: 13px;
                }}
                QPushButton#btnEditName:hover {{
                    background-color: {btn_hover};
                }}
            """)

        if hasattr(self, "btn_save_name"):
            self.btn_save_name.setStyleSheet("""
                QPushButton#btnSaveName {
                    background-color: #3B82F6;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-weight: 600;
                }
                QPushButton#btnSaveName:hover {
                    background-color: #2563EB;
                }
            """)

        if hasattr(self, "lbl_masked_token"):
            self.lbl_masked_token.setStyleSheet(
                f"color: {muted}; font-family: Consolas, monospace; font-size: 12px; background: transparent; border: none;"
            )

        if hasattr(self, "lbl_pinned_badge"):
            self.lbl_pinned_badge.setStyleSheet(
                f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 11px; font-weight: bold; background: transparent; border: none;"
            )

        if hasattr(self, "btn_theme"):
            if self.theme.mode == "light":
                theme_icon = "☀️ Light"
            elif self.theme.mode == "dark":
                theme_icon = "🌙 Dark"
            else:
                theme_icon = "💻 System"
            self.btn_theme.setText(theme_icon)

        if hasattr(self, "btn_delete"):
            self.btn_delete.setStyleSheet("""
                QPushButton#btnDelete {
                    background-color: transparent;
                    color: #EF4444;
                    border: 1px solid rgba(239, 68, 68, 0.4);
                    border-radius: 6px;
                    padding: 0px;
                    font-size: 13px;
                }
                QPushButton#btnDelete:hover {
                    background-color: rgba(239, 68, 68, 0.15);
                }
            """)

        self._update_pin_button()

        # 6. Budget Section
        if hasattr(self, "lbl_budget_title"):
            self.lbl_budget_title.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {text}; background: transparent; border: none;"
            )

        if hasattr(self, "lbl_last_updated"):
            self.lbl_last_updated.setStyleSheet(
                f"color: {muted}; font-size: 11px; background: transparent; border: none;"
            )

        if hasattr(self, "budget_card"):
            self.budget_card.setStyleSheet(f"""
                QWidget#budgetCard {{
                    background-color: {card_bg};
                    border: 1px solid {card_border};
                    border-radius: 12px;
                }}
            """)

        if hasattr(self, "detail_gauge"):
            self.detail_gauge.update()

        if hasattr(self, "card_spend"):
            self.card_spend.apply_theme()
            self.card_rem.apply_theme()
            self.card_limit.apply_theme()
            self.pill_today.apply_theme()
            self.pill_week.apply_theme()
            self.pill_month.apply_theme()

        # 7. Account Overview Section
        if hasattr(self, "lbl_account_title"):
            self.lbl_account_title.setStyleSheet(
                f"font-size: 15px; font-weight: bold; color: {sec}; margin-top: 8px; background: transparent; border: none;"
            )

        if hasattr(self, "acct_card"):
            acct_border = "rgba(59, 130, 246, 0.20)" if is_dark else "rgba(59, 130, 246, 0.25)"
            acct_bg = "rgba(59, 130, 246, 0.08)" if is_dark else "rgba(59, 130, 246, 0.06)"
            self.acct_card.setStyleSheet(f"""
                QWidget#acctCard {{
                    background-color: {acct_bg};
                    border: 1px solid {acct_border};
                    border-radius: 12px;
                }}
            """)

        if hasattr(self, "lbl_bal_caption"):
            self.lbl_bal_caption.setStyleSheet(
                f"color: {sec}; font-size: 12px; border: none; background: transparent;"
            )
        if hasattr(self, "lbl_tot_cap"):
            self.lbl_tot_cap.setStyleSheet(
                f"color: {sec}; font-size: 11px; border: none; background: transparent;"
            )
        if hasattr(self, "lbl_acct_total"):
            self.lbl_acct_total.setStyleSheet(
                f"color: {text}; font-size: 15px; font-family: Consolas, monospace; font-weight: 600; border: none; background: transparent;"
            )
        if hasattr(self, "lbl_burn_cap"):
            self.lbl_burn_cap.setStyleSheet(
                f"color: {sec}; font-size: 11px; border: none; background: transparent;"
            )
        if hasattr(self, "lbl_acct_burn"):
            self.lbl_acct_burn.setStyleSheet(
                f"color: {text}; font-size: 15px; font-family: Consolas, monospace; font-weight: 600; border: none; background: transparent;"
            )
        if hasattr(self, "lbl_bar_stat1"):
            self.lbl_bar_stat1.setStyleSheet(
                f"color: {muted}; font-size: 11px; border: none; background: transparent;"
            )
        if hasattr(self, "lbl_bar_stat2"):
            self.lbl_bar_stat2.setStyleSheet(
                f"color: {muted}; font-size: 11px; border: none; background: transparent;"
            )

    def _update_pin_button(self) -> None:
        if not hasattr(self, "btn_pin"):
            return
        is_dark = self.theme.is_dark()
        btn_bg = "#27272A" if is_dark else "#FFFFFF"
        btn_hover = "#3F3F46" if is_dark else "#F1F5F9"
        btn_border = "#3F3F46" if is_dark else "#CBD5E1"
        text = self.theme.text_primary

        key = next((k for k in self.keys if k.id == self.selected_key_id), None)
        is_pinned = key.is_widget_key if key else False

        if is_pinned:
            if hasattr(self, "lbl_pinned_badge"):
                self.lbl_pinned_badge.show()
            self.btn_pin.setText("Pinned to Widget")
            self.btn_pin.setStyleSheet(f"""
                QPushButton#btnPin {{
                    background-color: {OpenRouterTheme.ELECTRIC_BLUE};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 600;
                }}
                QPushButton#btnPin:hover {{
                    background-color: #2563EB;
                }}
            """)
        else:
            if hasattr(self, "lbl_pinned_badge"):
                self.lbl_pinned_badge.hide()
            self.btn_pin.setText("Pin to Widget")
            self.btn_pin.setStyleSheet(f"""
                QPushButton#btnPin {{
                    background-color: {btn_bg};
                    color: {text};
                    border: 1px solid {btn_border};
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 600;
                }}
                QPushButton#btnPin:hover {{
                    background-color: {btn_hover};
                }}
            """)

    def _build_empty_view(self) -> None:
        self.empty_widget = QWidget()
        self.empty_widget.setObjectName("emptyWidget")
        layout = QVBoxLayout(self.empty_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon_lbl = QLabel("🔑")
        icon_lbl.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_empty_title = QLabel("No API Keys Added")
        self.lbl_empty_title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {self.theme.text_primary}; background: transparent; border: none;"
        )
        layout.addWidget(self.lbl_empty_title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.lbl_empty_sub = QLabel("Add your OpenRouter key to track usage, balance, and desktop widgets.")
        self.lbl_empty_sub.setStyleSheet(
            f"color: {self.theme.text_muted}; font-size: 13px; background: transparent; border: none;"
        )
        layout.addWidget(self.lbl_empty_sub, alignment=Qt.AlignmentFlag.AlignCenter)

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

        self.detail_stack.addWidget(self.empty_widget)

    def _build_detail_view(self) -> None:
        self.scroll = QScrollArea()
        self.scroll.setObjectName("detailScrollArea")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.viewport().setObjectName("detailViewport")

        self.detail_container = QWidget()
        self.detail_container.setObjectName("detailContainer")
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setContentsMargins(28, 24, 28, 24)
        self.detail_layout.setSpacing(22)

        self._build_header_card()
        self._build_budget_section()
        self._build_account_section()

        self.detail_layout.addStretch()
        self.scroll.setWidget(self.detail_container)
        self.detail_stack.addWidget(self.scroll)

    def _build_header_card(self) -> None:
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(6)

        # Top row: Key Name on Left, Actions on Right
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        edit_row = QHBoxLayout()
        edit_row.setSpacing(8)

        self.lbl_key_name = QLabel("API Key")
        self.lbl_key_name.setObjectName("lblKeyName")
        self.lbl_key_name.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {self.theme.text_primary}; background: transparent; border: none;"
        )
        edit_row.addWidget(self.lbl_key_name)

        self.txt_edit_name = QLineEdit()
        self.txt_edit_name.setObjectName("txtEditName")
        self.txt_edit_name.setStyleSheet(f"""
            QLineEdit#txtEditName {{
                background-color: {self.theme.card_bg};
                color: {self.theme.text_primary};
                border: 1px solid #3B82F6;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 15px;
            }}
        """)
        self.txt_edit_name.hide()
        edit_row.addWidget(self.txt_edit_name)

        self.btn_edit_name = QPushButton("✏️")
        self.btn_edit_name.setObjectName("btnEditName")
        self.btn_edit_name.setFixedSize(28, 28)
        self.btn_edit_name.setToolTip("Rename Key")
        self.btn_edit_name.clicked.connect(self._toggle_edit_name)
        edit_row.addWidget(self.btn_edit_name)

        self.btn_save_name = QPushButton("Save")
        self.btn_save_name.setObjectName("btnSaveName")
        self.btn_save_name.setStyleSheet("background-color: #3B82F6; color: white;")
        self.btn_save_name.hide()
        self.btn_save_name.clicked.connect(self._save_edited_name)
        edit_row.addWidget(self.btn_save_name)

        top_row.addLayout(edit_row)
        top_row.addStretch()

        # Right Action Buttons
        actions_hbox = QHBoxLayout()
        actions_hbox.setSpacing(8)

        # Theme Switcher Button
        self.btn_theme = QPushButton("💻 System")
        self.btn_theme.setObjectName("btnTheme")
        self.btn_theme.setToolTip("Switch Theme (System / Dark / Light)")
        self.btn_theme.clicked.connect(self._cycle_theme)
        actions_hbox.addWidget(self.btn_theme)

        self.btn_pin = QPushButton("Pin to Widget")
        self.btn_pin.setObjectName("btnPin")
        self.btn_pin.clicked.connect(self._toggle_pin_widget)
        actions_hbox.addWidget(self.btn_pin)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setObjectName("btnRefresh")
        self.btn_refresh.clicked.connect(self._refresh_selected_key)
        actions_hbox.addWidget(self.btn_refresh)

        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setObjectName("btnDelete")
        self.btn_delete.setFixedSize(30, 30)
        self.btn_delete.setToolTip("Delete Key")
        self.btn_delete.clicked.connect(self._delete_selected_key)
        actions_hbox.addWidget(self.btn_delete)

        top_row.addLayout(actions_hbox)
        header_vbox.addLayout(top_row)

        # Sub row: Token and Active Widget Badge
        sub_row = QHBoxLayout()
        sub_row.setSpacing(10)
        self.lbl_masked_token = QLabel("Token: ••••••••")
        self.lbl_masked_token.setObjectName("lblMaskedToken")
        self.lbl_masked_token.setStyleSheet(
            f"color: {self.theme.text_muted}; font-family: Consolas, monospace; font-size: 12px; background: transparent; border: none;"
        )
        sub_row.addWidget(self.lbl_masked_token)

        self.lbl_pinned_badge = QLabel("✓ Active on Desktop Widget")
        self.lbl_pinned_badge.setObjectName("lblPinnedBadge")
        self.lbl_pinned_badge.setStyleSheet(
            f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 11px; font-weight: bold; background: transparent; border: none;"
        )
        sub_row.addWidget(self.lbl_pinned_badge)
        sub_row.addStretch()

        header_vbox.addLayout(sub_row)
        self.detail_layout.addLayout(header_vbox)

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

    def _cycle_theme(self) -> None:
        order = ["system", "light", "dark"]
        curr_idx = order.index(self.theme.mode) if self.theme.mode in order else 0
        next_mode = order[(curr_idx + 1) % len(order)]
        self.theme.set_mode(next_mode)

    def _build_budget_section(self) -> None:
        sec_header = QHBoxLayout()
        self.lbl_budget_title = QLabel("Key Budget & Usage")
        self.lbl_budget_title.setObjectName("lblBudgetTitle")
        self.lbl_budget_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {self.theme.text_primary}; background: transparent; border: none;"
        )
        sec_header.addWidget(self.lbl_budget_title)
        sec_header.addStretch()

        self.lbl_last_updated = QLabel("Updated just now")
        self.lbl_last_updated.setObjectName("lblLastUpdated")
        self.lbl_last_updated.setStyleSheet(
            f"color: {self.theme.text_muted}; font-size: 11px; background: transparent; border: none;"
        )
        sec_header.addWidget(self.lbl_last_updated)
        self.detail_layout.addLayout(sec_header)

        self.budget_card = QWidget()
        self.budget_card.setObjectName("budgetCard")
        card_layout = QHBoxLayout(self.budget_card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(24)

        self.detail_gauge = RadialGauge(stroke_width=11.0)
        self.detail_gauge.setFixedSize(116, 116)
        card_layout.addWidget(self.detail_gauge)

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
        self.detail_layout.addWidget(self.budget_card)

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
        self.lbl_account_title = QLabel("Account Overview (Shared Balance)")
        self.lbl_account_title.setObjectName("lblAccountTitle")
        self.lbl_account_title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; color: {self.theme.text_secondary}; margin-top: 8px; background: transparent; border: none;"
        )
        self.detail_layout.addWidget(self.lbl_account_title)

        self.acct_card = QWidget()
        self.acct_card.setObjectName("acctCard")
        acct_layout = QVBoxLayout(self.acct_card)
        acct_layout.setContentsMargins(18, 16, 18, 16)
        acct_layout.setSpacing(14)

        top_row = QHBoxLayout()
        bal_vbox = QVBoxLayout()
        bal_vbox.setSpacing(2)
        self.lbl_bal_caption = QLabel("Available Account Balance")
        self.lbl_bal_caption.setObjectName("lblBalCaption")
        self.lbl_bal_caption.setStyleSheet(
            f"color: {self.theme.text_secondary}; font-size: 12px; border: none; background: transparent;"
        )
        self.lbl_acct_bal = QLabel("$0.00")
        self.lbl_acct_bal.setObjectName("lblAcctBal")
        self.lbl_acct_bal.setStyleSheet(
            f"color: {OpenRouterTheme.ELECTRIC_BLUE}; font-size: 26px; font-weight: bold; border: none; background: transparent;"
        )
        bal_vbox.addWidget(self.lbl_bal_caption)
        bal_vbox.addWidget(self.lbl_acct_bal)
        top_row.addLayout(bal_vbox)

        top_row.addStretch()

        totals_hbox = QHBoxLayout()
        totals_hbox.setSpacing(20)
        tot_vbox = QVBoxLayout()
        tot_vbox.setSpacing(2)
        self.lbl_tot_cap = QLabel("Total Purchased")
        self.lbl_tot_cap.setObjectName("lblTotCap")
        self.lbl_tot_cap.setStyleSheet(
            f"color: {self.theme.text_secondary}; font-size: 11px; border: none; background: transparent;"
        )
        self.lbl_acct_total = QLabel("$0.00")
        self.lbl_acct_total.setObjectName("lblAcctTotal")
        self.lbl_acct_total.setStyleSheet(
            f"color: {self.theme.text_primary}; font-size: 15px; font-family: Consolas, monospace; font-weight: 600; border: none; background: transparent;"
        )
        tot_vbox.addWidget(self.lbl_tot_cap)
        tot_vbox.addWidget(self.lbl_acct_total)
        totals_hbox.addLayout(tot_vbox)

        burn_vbox = QVBoxLayout()
        burn_vbox.setSpacing(2)
        self.lbl_burn_cap = QLabel("Account Burn")
        self.lbl_burn_cap.setObjectName("lblBurnCap")
        self.lbl_burn_cap.setStyleSheet(
            f"color: {self.theme.text_secondary}; font-size: 11px; border: none; background: transparent;"
        )
        self.lbl_acct_burn = QLabel("$0.00")
        self.lbl_acct_burn.setObjectName("lblAcctBurn")
        self.lbl_acct_burn.setStyleSheet(
            f"color: {self.theme.text_primary}; font-size: 15px; font-family: Consolas, monospace; font-weight: 600; border: none; background: transparent;"
        )
        burn_vbox.addWidget(self.lbl_burn_cap)
        burn_vbox.addWidget(self.lbl_acct_burn)
        totals_hbox.addLayout(burn_vbox)

        top_row.addLayout(totals_hbox)
        acct_layout.addLayout(top_row)

        self.account_bar = AccountBurnBar()
        acct_layout.addWidget(self.account_bar)

        sub_stats = QHBoxLayout()
        self.lbl_bar_stat1 = QLabel("Total used: $0.00 (0%)")
        self.lbl_bar_stat1.setObjectName("lblBarStat1")
        self.lbl_bar_stat1.setStyleSheet(
            f"color: {self.theme.text_muted}; font-size: 11px; border: none; background: transparent;"
        )
        self.lbl_bar_stat2 = QLabel("Credits pool: $0.00")
        self.lbl_bar_stat2.setObjectName("lblBarStat2")
        self.lbl_bar_stat2.setStyleSheet(
            f"color: {self.theme.text_muted}; font-size: 11px; border: none; background: transparent;"
        )
        sub_stats.addWidget(self.lbl_bar_stat1)
        sub_stats.addStretch()
        sub_stats.addWidget(self.lbl_bar_stat2)
        acct_layout.addLayout(sub_stats)

        self.detail_layout.addWidget(self.acct_card)

    def _on_theme_changed(self) -> None:
        self._apply_theme_styles()
        self.load_all_data()

    def load_all_data(self) -> None:
        self.keys = SharedStorage.load_all_keys()
        self.list_keys.clear()

        for k in self.keys:
            payload = SharedStorage.get_payload(k.id)
            if payload:
                self.payloads[k.id] = payload

            item = QListWidgetItem(self.list_keys)
            item.setSizeHint(QSize(240, 54))
            widget = KeyListItemWidget(k, payload)
            self.list_keys.setItemWidget(item, widget)

        if not self.keys:
            self.detail_stack.setCurrentIndex(0)
            self.selected_key_id = None
        else:
            self.detail_stack.setCurrentIndex(1)
            sel_idx = 0
            if self.selected_key_id:
                match_idx = next((i for i, k in enumerate(self.keys) if k.id == self.selected_key_id), -1)
                if match_idx >= 0:
                    sel_idx = match_idx
                else:
                    sel_idx = next((i for i, k in enumerate(self.keys) if k.is_widget_key), 0)
            else:
                sel_idx = next((i for i, k in enumerate(self.keys) if k.is_widget_key), 0)

            self.list_keys.setCurrentRow(sel_idx)
            for i in range(self.list_keys.count()):
                w = self.list_keys.itemWidget(self.list_keys.item(i))
                if isinstance(w, KeyListItemWidget):
                    w.set_selected(i == sel_idx)

    def _on_key_selected(self, row: int) -> None:
        if row < 0 or row >= len(self.keys):
            return

        for i in range(self.list_keys.count()):
            w = self.list_keys.itemWidget(self.list_keys.item(i))
            if isinstance(w, KeyListItemWidget):
                w.set_selected(i == row)

        key = self.keys[row]
        self.selected_key_id = key.id
        self._display_key(key)

    def _display_key(self, key: TrackedKey) -> None:
        key_name = key.custom_label if key.custom_label and key.custom_label.strip() else "API Key"
        self.lbl_key_name.setText(key_name)
        self.lbl_key_name.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {self.theme.text_primary}; background: transparent; border: none;"
        )
        self.txt_edit_name.setText(key_name)
        self.lbl_masked_token.setText(f"Token: {key.key_masked}")

        self._update_pin_button()

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
        self.account_bar.set_percent(payload.account_burn_percent)

        self.update()

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
