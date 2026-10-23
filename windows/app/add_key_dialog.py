"""Modal dialog to add, test, and save an OpenRouter API key."""

from __future__ import annotations

import threading
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from windows.core.models import OpenRouterTheme, TrackedKey, WidgetPayload
from windows.core.service import OpenRouterService
from windows.core.storage import SharedStorage
from windows.core.theme import ThemeManager


class AddKeyDialog(QDialog):
    key_validated_and_added = Signal(object)  # Emits TrackedKey
    _test_finished = Signal(object)          # Internal signal: Emits WidgetPayload
    _save_finished = Signal(object, object)  # Internal signal: Emits (TrackedKey, WidgetPayload)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add OpenRouter API Key")
        self.setFixedWidth(460)
        self.setModal(True)
        self._is_testing: bool = False
        self._verified_payload: Optional[WidgetPayload] = None
        self._verified_key_str: Optional[str] = None

        self.theme = ThemeManager.get_instance()
        self.theme.theme_changed.connect(self.apply_theme)

        self._init_ui()
        self._test_finished.connect(self._on_test_finished)
        self._save_finished.connect(self._on_save_finished)
        self.apply_theme()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.title_lbl = QLabel("Add New OpenRouter Key")
        self.title_lbl.setStyleSheet("font-size: 17px; font-weight: bold;")
        layout.addWidget(self.title_lbl)

        # Custom Nickname Input
        self.lbl_nick = QLabel("Custom Nickname")
        self.lbl_nick.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.txt_nickname = QLineEdit()
        self.txt_nickname.setPlaceholderText("e.g. Work Backend, Personal Project")
        layout.addWidget(self.lbl_nick)
        layout.addWidget(self.txt_nickname)

        # API Key Input
        self.lbl_key = QLabel("API Key")
        self.lbl_key.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.txt_key = QLineEdit()
        self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_key.setPlaceholderText("sk-or-v1-...")
        self.txt_key.textChanged.connect(self._on_key_text_changed)
        layout.addWidget(self.lbl_key)
        layout.addWidget(self.txt_key)

        # Pin to widget checkbox
        self.chk_widget = QCheckBox("Pin to Desktop Widget")
        self.chk_widget.setChecked(True)
        layout.addWidget(self.chk_widget)

        # Status & Feedback banner (handles error and success messages)
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.hide()
        layout.addWidget(self.lbl_status)

        # Bottom Buttons: Cancel | Spacer | Test Key | Save Key
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_test = QPushButton("Test Key")
        self.btn_test.setObjectName("testBtn")
        self.btn_test.setEnabled(False)
        self.btn_test.clicked.connect(self._run_test_only)
        btn_layout.addWidget(self.btn_test)

        self.btn_save = QPushButton("Save Key")
        self.btn_save.setObjectName("saveBtn")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._run_save)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def apply_theme(self) -> None:
        is_dark = self.theme.is_dark()
        bg = "#1E1E24" if is_dark else "#FFFFFF"
        text = "#F4F4F5" if is_dark else "#0F172A"
        sec = "#A1A1AA" if is_dark else "#64748B"
        input_bg = "#27272A" if is_dark else "#F8FAFC"
        input_border = "#3F3F46" if is_dark else "#CBD5E1"
        btn_bg = "#27272A" if is_dark else "#F1F5F9"
        btn_border = "#3F3F46" if is_dark else "#CBD5E1"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                color: {text};
            }}
            QLabel {{
                color: {text};
            }}
            QLineEdit {{
                background-color: {input_bg};
                color: {text};
                border: 1px solid {input_border};
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid #3B82F6;
            }}
            QCheckBox {{
                color: {text};
                spacing: 8px;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text};
                border: 1px solid {btn_border};
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {'#3F3F46' if is_dark else '#E2E8F0'};
            }}
            QPushButton#testBtn {{
                background-color: {btn_bg};
                color: #38BDF8;
                border: 1px solid rgba(56, 189, 248, 0.4);
            }}
            QPushButton#testBtn:hover {{
                background-color: rgba(56, 189, 248, 0.15);
            }}
            QPushButton#saveBtn {{
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
            }}
            QPushButton#saveBtn:hover {{
                background-color: #2563EB;
            }}
            QPushButton#saveBtn:disabled, QPushButton#testBtn:disabled {{
                background-color: {btn_bg};
                color: {'#55555C' if is_dark else '#94A3B8'};
                border-color: {btn_border};
            }}
        """)

        if hasattr(self, "title_lbl"):
            self.title_lbl.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {text};")
        if hasattr(self, "lbl_nick"):
            self.lbl_nick.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {sec};")
        if hasattr(self, "lbl_key"):
            self.lbl_key.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {sec};")

    def _on_key_text_changed(self) -> None:
        key_text = self.txt_key.text().strip()
        has_key = len(key_text) > 8

        # Invalidate previous verification if key modified
        if self._verified_key_str != key_text:
            self._verified_payload = None
            self._verified_key_str = None
            self.lbl_status.hide()

        self.btn_test.setEnabled(has_key and not self._is_testing)
        self.btn_save.setEnabled(has_key and not self._is_testing)

    def _set_buttons_testing(self, testing: bool, testing_save: bool = False) -> None:
        self._is_testing = testing
        self.txt_key.setEnabled(not testing)
        self.txt_nickname.setEnabled(not testing)
        self.btn_cancel.setEnabled(not testing)

        if testing:
            if testing_save:
                self.btn_save.setEnabled(False)
                self.btn_save.setText("Verifying & Saving...")
                self.btn_test.setEnabled(False)
            else:
                self.btn_test.setEnabled(False)
                self.btn_test.setText("Testing...")
                self.btn_save.setEnabled(False)
        else:
            self.btn_test.setText("Test Key")
            self.btn_save.setText("Save Key")
            self._on_key_text_changed()

    # MARK: - Separate "Test Key" Action

    def _run_test_only(self) -> None:
        raw_key = self.txt_key.text().strip()
        label = self.txt_nickname.text().strip() or "API Key"
        if not raw_key:
            return

        self._set_buttons_testing(True, testing_save=False)
        self.lbl_status.hide()

        def worker():
            try:
                payload = OpenRouterService.fetch_data(raw_key, label)
            except Exception as e:
                payload = WidgetPayload.empty()
                payload.error_message = f"Error: {e}"
            self._test_finished.emit(payload)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_test_finished(self, payload: WidgetPayload) -> None:
        self._set_buttons_testing(False)
        current_key = self.txt_key.text().strip()

        if payload.error_message:
            self.lbl_status.setText(f"❌ {payload.error_message}")
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(239, 68, 68, 0.12);
                    color: {OpenRouterTheme.CORAL_RED};
                    border: 1px solid rgba(239, 68, 68, 0.35);
                    border-radius: 6px;
                    padding: 8px 10px;
                    font-size: 11px;
                }}
            """)
            self.lbl_status.show()
            self._verified_payload = None
            self._verified_key_str = None
        else:
            self._verified_payload = payload
            self._verified_key_str = current_key

            info = f"✓ Verified! Total pool: ${payload.total_balance:.2f}"
            if payload.key_limit is not None and payload.key_limit > 0:
                info += f" | Key limit: ${payload.key_limit:.2f} (Remaining: ${payload.key_remaining:.2f})"
            else:
                info += f" | Key spent: ${payload.key_usage:.4f} (Unlimited)"

            self.lbl_status.setText(info)
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(16, 185, 129, 0.12);
                    color: {OpenRouterTheme.EMERALD_GREEN};
                    border: 1px solid rgba(16, 185, 129, 0.35);
                    border-radius: 6px;
                    padding: 8px 10px;
                    font-size: 11px;
                }}
            """)
            self.lbl_status.show()

    # MARK: - Separate "Save Key" Action

    def _run_save(self) -> None:
        raw_key = self.txt_key.text().strip()
        label = self.txt_nickname.text().strip() or "API Key"
        is_widget = self.chk_widget.isChecked()

        if not raw_key:
            return

        # If already tested and verified, save directly without redundant network call
        if self._verified_payload and self._verified_key_str == raw_key and not self._verified_payload.error_message:
            self._persist_and_close(raw_key, label, is_widget, self._verified_payload)
            return

        # If not yet tested, verify and save in background
        self._set_buttons_testing(True, testing_save=True)
        self.lbl_status.hide()

        def worker():
            try:
                payload = OpenRouterService.fetch_data(raw_key, label)
            except Exception as e:
                payload = WidgetPayload.empty()
                payload.error_message = f"Error: {e}"

            if not payload.error_message:
                new_key = SharedStorage.add_key(label, raw_key, is_widget_key=is_widget)
                SharedStorage.save_payload(payload, new_key.id)
                if is_widget:
                    SharedStorage.save_widget_payload(payload)
                self._save_finished.emit(new_key, payload)
            else:
                self._save_finished.emit(None, payload)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_save_finished(self, new_key: Optional[TrackedKey], payload: WidgetPayload) -> None:
        self._set_buttons_testing(False)

        if payload.error_message or new_key is None:
            self.lbl_status.setText(f"❌ {payload.error_message or 'Could not validate key'}")
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(239, 68, 68, 0.12);
                    color: {OpenRouterTheme.CORAL_RED};
                    border: 1px solid rgba(239, 68, 68, 0.35);
                    border-radius: 6px;
                    padding: 8px 10px;
                    font-size: 11px;
                }}
            """)
            self.lbl_status.show()
            return

        self.key_validated_and_added.emit(new_key)
        self.accept()

    def _persist_and_close(
        self, raw_key: str, label: str, is_widget: bool, payload: WidgetPayload
    ) -> None:
        new_key = SharedStorage.add_key(label, raw_key, is_widget_key=is_widget)
        SharedStorage.save_payload(payload, new_key.id)
        if is_widget:
            SharedStorage.save_widget_payload(payload)
        self.key_validated_and_added.emit(new_key)
        self.accept()
