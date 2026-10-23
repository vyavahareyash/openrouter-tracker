"""Modal dialog to add and live-validate a new OpenRouter API key."""

from __future__ import annotations

import threading
from typing import Callable, Optional

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


class AddKeyDialog(QDialog):
    key_validated_and_added = Signal(object)  # Emits TrackedKey

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Add OpenRouter API Key")
        self.setFixedWidth(420)
        self.setModal(True)
        self._is_testing: bool = False

        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E24;
                color: #F4F4F5;
            }
            QLabel {
                color: #E4E4E7;
            }
            QLineEdit {
                background-color: #27272A;
                color: #FFFFFF;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            QCheckBox {
                color: #D4D4D8;
                spacing: 8px;
            }
            QPushButton {
                background-color: #27272A;
                color: #F4F4F5;
                border: 1px solid #3F3F46;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #3F3F46;
            }
            QPushButton#saveBtn {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
            }
            QPushButton#saveBtn:hover {
                background-color: #2563EB;
            }
            QPushButton#saveBtn:disabled {
                background-color: #1E3A8A;
                color: #64748B;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Add New OpenRouter Key")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)

        # Custom Nickname Input
        lbl_nick = QLabel("Custom Nickname")
        lbl_nick.setStyleSheet("font-size: 11px; font-weight: bold; color: #A1A1AA;")
        self.txt_nickname = QLineEdit()
        self.txt_nickname.setPlaceholderText("e.g. Work Backend, Personal Project")
        layout.addWidget(lbl_nick)
        layout.addWidget(self.txt_nickname)

        # API Key Input
        lbl_key = QLabel("API Key")
        lbl_key.setStyleSheet("font-size: 11px; font-weight: bold; color: #A1A1AA;")
        self.txt_key = QLineEdit()
        self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_key.setPlaceholderText("sk-or-v1-...")
        self.txt_key.textChanged.connect(self._validate_input)
        layout.addWidget(lbl_key)
        layout.addWidget(self.txt_key)

        # Pin to widget checkbox
        self.chk_widget = QCheckBox("Pin to Desktop Widget")
        self.chk_widget.setChecked(True)
        layout.addWidget(self.chk_widget)

        # Error display label
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet(f"color: {OpenRouterTheme.CORAL_RED}; font-size: 11px;")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.hide()
        layout.addWidget(self.lbl_error)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_save = QPushButton("Test & Save Key")
        self.btn_save.setObjectName("saveBtn")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._test_and_save)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _validate_input(self) -> None:
        key_text = self.txt_key.text().strip()
        self.btn_save.setEnabled(len(key_text) > 5 and not self._is_testing)

    def _test_and_save(self) -> None:
        raw_key = self.txt_key.text().strip()
        label = self.txt_nickname.text().strip()
        is_widget = self.chk_widget.isChecked()

        if not raw_key:
            return

        self._is_testing = True
        self.btn_save.setEnabled(False)
        self.btn_save.setText("Testing Key...")
        self.lbl_error.hide()

        def worker():
            payload = OpenRouterService.fetch_data(raw_key, label)
            # Call completion on Qt thread
            self._on_test_complete(raw_key, label, is_widget, payload)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _on_test_complete(
        self, raw_key: str, label: str, is_widget: bool, payload: WidgetPayload
    ) -> None:
        # Check error on main thread
        from PySide6.QtCore import QMetaObject, Q_ARG

        def apply_result():
            self._is_testing = False
            self.btn_save.setEnabled(True)
            self.btn_save.setText("Test & Save Key")

            if payload.error_message:
                self.lbl_error.setText(f"❌ {payload.error_message}")
                self.lbl_error.show()
                return

            # Success: persist key and payload
            new_key = SharedStorage.add_key(label, raw_key, is_widget_key=is_widget)
            SharedStorage.save_payload(payload, new_key.id)
            if is_widget:
                SharedStorage.save_widget_payload(payload)

            self.key_validated_and_added.emit(new_key)
            self.accept()

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, apply_result)
