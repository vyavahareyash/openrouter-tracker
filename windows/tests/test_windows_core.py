"""Unit tests for OpenRouter Tracker Windows core, models, storage, and service using unittest."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from windows.core.models import OpenRouterTheme, TrackedKey, WidgetPayload
from windows.core.service import OpenRouterService
from windows.core.storage import SharedStorage


class TestModels(unittest.TestCase):
    def test_key_masking(self):
        short_key = "sk-12345"
        self.assertEqual(TrackedKey.mask(short_key), "••••••••")

        standard_key = "sk-or-v1-mock-test-sample-key-12345678"
        masked = TrackedKey.mask(standard_key)
        self.assertTrue(masked.startswith("sk-or-v1"))
        self.assertTrue(masked.endswith("5678"))
        self.assertIn("...", masked)

    def test_widget_payload_math(self):
        payload = WidgetPayload(
            key_usage=3.5,
            key_limit=5.0,
            key_remaining=1.5,
            total_credits=100.0,
            total_usage=25.0,
            total_balance=75.0,
        )
        self.assertAlmostEqual(payload.usage_percent, 0.70)
        self.assertAlmostEqual(payload.account_burn_percent, 0.25)
        self.assertTrue(payload.is_low_balance)
        self.assertTrue(payload.is_critical_balance)

    def test_widget_payload_serialization(self):
        payload = WidgetPayload.placeholder()
        p_dict = payload.to_dict()
        reconstituted = WidgetPayload.from_dict(p_dict)
        self.assertEqual(reconstituted.key_usage, payload.key_usage)
        self.assertEqual(reconstituted.total_credits, payload.total_credits)
        self.assertEqual(reconstituted.custom_nickname, payload.custom_nickname)

    def test_theme_color_thresholds(self):
        self.assertEqual(OpenRouterTheme.get_gauge_color(0.50), OpenRouterTheme.ELECTRIC_BLUE)
        self.assertEqual(OpenRouterTheme.get_gauge_color(0.80), OpenRouterTheme.AMBER_WARNING)
        self.assertEqual(OpenRouterTheme.get_gauge_color(0.95), OpenRouterTheme.CORAL_RED)


class TestSharedStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ort_test_"))
        self.old_custom = SharedStorage.custom_storage_directory
        SharedStorage.custom_storage_directory = self.temp_dir

    def tearDown(self):
        SharedStorage.custom_storage_directory = self.old_custom
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_key_lifecycle_and_dpapi_encryption(self):
        # 1. Add first key (should automatically become active widget key)
        raw_key_1 = "sk-or-v1-first-sample-key-1234567890"
        key_1 = SharedStorage.add_key("Primary Project", raw_key_1)
        self.assertTrue(key_1.is_widget_key)
        self.assertEqual(key_1.custom_label, "Primary Project")

        # Verify DPAPI hardware-backed encryption
        retrieved_raw = SharedStorage.get_raw_api_key(key_1.id)
        self.assertEqual(retrieved_raw, raw_key_1)

        # 2. Add second key without widget flag
        raw_key_2 = "sk-or-v1-second-sample-key-9876543210"
        key_2 = SharedStorage.add_key("Secondary Client", raw_key_2, is_widget_key=False)
        self.assertFalse(key_2.is_widget_key)

        all_keys = SharedStorage.load_all_keys()
        self.assertEqual(len(all_keys), 2)

        # 3. Switch active widget key
        SharedStorage.set_widget_key(key_2.id)
        widget_key = SharedStorage.get_widget_key()
        self.assertIsNotNone(widget_key)
        self.assertEqual(widget_key.id, key_2.id)

        # 4. Save and load payload
        test_payload = WidgetPayload(
            key_usage=4.20,
            key_limit=10.0,
            key_remaining=5.80,
            custom_nickname="Secondary Client",
        )
        SharedStorage.save_payload(test_payload, key_2.id)
        loaded = SharedStorage.get_payload(key_2.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.key_usage, 4.20)

        # 5. Delete active widget key (should promote remaining key)
        SharedStorage.delete_key(key_2.id)
        remaining_keys = SharedStorage.load_all_keys()
        self.assertEqual(len(remaining_keys), 1)
        self.assertEqual(remaining_keys[0].id, key_1.id)
        self.assertTrue(remaining_keys[0].is_widget_key)

    def test_settings_persistence(self):
        SharedStorage.set_setting("widget_mode", "small")
        SharedStorage.set_setting("widget_x", 450)
        self.assertEqual(SharedStorage.get_setting("widget_mode"), "small")
        self.assertEqual(SharedStorage.get_setting("widget_x"), 450)
        self.assertEqual(SharedStorage.get_setting("non_existent", default=42), 42)


class TestOpenRouterService(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_fetch_data_success(self, mock_urlopen):
        # Mock auth key response context manager
        mock_key_resp = MagicMock()
        mock_key_resp.status = 200
        mock_key_resp.read.return_value = json.dumps({
            "data": {
                "label": "Prod Agent Key",
                "usage": 2.50,
                "limit": 10.0,
                "is_free_tier": False,
                "usage_daily": 0.50,
                "usage_weekly": 1.25,
                "usage_monthly": 2.50,
            }
        }).encode("utf-8")

        mock_cm_key = MagicMock()
        mock_cm_key.__enter__.return_value = mock_key_resp

        # Mock credits response context manager
        mock_credits_resp = MagicMock()
        mock_credits_resp.status = 200
        mock_credits_resp.read.return_value = json.dumps({
            "data": {
                "total_credits": 200.0,
                "total_usage": 50.0,
            }
        }).encode("utf-8")

        mock_cm_credits = MagicMock()
        mock_cm_credits.__enter__.return_value = mock_credits_resp

        mock_urlopen.side_effect = [mock_cm_key, mock_cm_credits]

        payload = OpenRouterService.fetch_data("sk-or-v1-valid-key", "Prod Agent")
        self.assertIsNone(payload.error_message)
        self.assertEqual(payload.key_label, "Prod Agent Key")
        self.assertEqual(payload.key_usage, 2.50)
        self.assertEqual(payload.key_limit, 10.0)
        self.assertEqual(payload.key_remaining, 7.50)
        self.assertEqual(payload.total_credits, 200.0)
        self.assertEqual(payload.total_usage, 50.0)
        self.assertEqual(payload.total_balance, 150.0)

    def test_fetch_data_empty_key(self):
        payload = OpenRouterService.fetch_data("", "Test")
        self.assertEqual(payload.error_message, "API key not configured")


class TestUIComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        from PySide6.QtWidgets import QApplication
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ort_ui_test_"))
        self.old_custom = SharedStorage.custom_storage_directory
        SharedStorage.custom_storage_directory = self.temp_dir

    def tearDown(self):
        SharedStorage.custom_storage_directory = self.old_custom
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_radial_gauge_initialization_and_payload(self):
        from windows.widget.radial_gauge import RadialGauge
        gauge = RadialGauge(stroke_width=8.0)
        payload = WidgetPayload.placeholder()
        gauge.set_payload(payload)
        self.assertIsNotNone(gauge.payload)
        self.assertEqual(gauge.payload.key_usage, 3.46)

    def test_desktop_widget_modes(self):
        from windows.widget.desktop_widget import DesktopWidget
        widget = DesktopWidget()
        self.assertEqual(widget.mode, "medium")

        widget.set_mode("small")
        self.assertEqual(widget.mode, "small")
        self.assertEqual(widget.size(), DesktopWidget.SMALL_SIZE)

        widget.set_mode("medium")
        self.assertEqual(widget.mode, "medium")
        self.assertEqual(widget.size(), DesktopWidget.MEDIUM_SIZE)

    def test_main_window_empty_and_populated(self):
        from windows.app.main_window import MainWindow
        win = MainWindow()
        # Initially empty stack index 0
        self.assertEqual(win.detail_stack.currentIndex(), 0)

        # Add key and verify it switches to populated view
        key = SharedStorage.add_key("Test Agent", "sk-or-v1-mock-test-sample-key-12345678")
        win.load_all_data()
        self.assertEqual(win.detail_stack.currentIndex(), 1)
        self.assertEqual(len(win.keys), 1)
        self.assertEqual(win.keys[0].id, key.id)

    def test_add_key_dialog_separate_buttons_and_signals(self):
        from windows.app.add_key_dialog import AddKeyDialog
        dlg = AddKeyDialog()

        # Verify buttons are distinct
        self.assertIsNotNone(dlg.btn_test)
        self.assertIsNotNone(dlg.btn_save)
        self.assertEqual(dlg.btn_test.text(), "Test Key")
        self.assertEqual(dlg.btn_save.text(), "Save Key")
        self.assertFalse(dlg.btn_test.isEnabled())
        self.assertFalse(dlg.btn_save.isEnabled())

        # Typing valid length key enables both buttons
        dlg.txt_key.setText("sk-or-v1-sample-api-key-test")
        self.assertTrue(dlg.btn_test.isEnabled())
        self.assertTrue(dlg.btn_save.isEnabled())

        # Test callback handles payload via Qt signals without getting stuck
        mock_payload = WidgetPayload(total_balance=100.0, total_credits=100.0, total_usage=0.0)
        dlg._on_test_finished(mock_payload)
        self.assertFalse(dlg._is_testing)
        self.assertEqual(dlg.btn_test.text(), "Test Key")
        self.assertFalse(dlg.lbl_status.isHidden())
        self.assertIn("Verified", dlg.lbl_status.text())


if __name__ == "__main__":
    unittest.main()
